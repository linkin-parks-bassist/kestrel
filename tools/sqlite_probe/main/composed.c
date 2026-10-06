#include "sqlite3.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <string.h>

int probe_sd_publish(sqlite3 **);
int probe_sd_reopen(sqlite3 **);
void probe_read_reset(void);
void probe_read_report(int,int,int);

/* Deliberately synthetic distributions; this is not the production schema. */
#ifndef KT_PROBE_ROWS
#define KT_PROBE_ROWS 10000
#endif
#define ROWS KT_PROBE_ROWS
#define STRINGIFY_VALUE(x) #x
#define STRINGIFY(x) STRINGIFY_VALUE(x)
#define HAS(axis,value) "EXISTS(SELECT 1 FROM facet WHERE axis='" axis "' AND value='" value "' AND effect_id=c.id)"
#define IDS(axis,value) "SELECT effect_id AS id FROM facet WHERE axis='" axis "' AND value='" value "'"
static const struct {
    const char *predicate;
    const char *axis;
    const char *value;
    const char *ids;
} cases[] = {
    {HAS("instrument","bass") " AND (" HAS("type","delay") " OR " HAS("type","modulation") ")", "instrument", "bass",
     IDS("instrument","bass") " INTERSECT SELECT id FROM (" IDS("type","delay") " UNION " IDS("type","modulation") ")"},
    {"(" HAS("instrument","bass") " OR " HAS("instrument","keys") ") AND " HAS("genre","ambient"), "genre", "ambient",
     "SELECT id FROM (" IDS("instrument","bass") " UNION " IDS("instrument","keys") ") INTERSECT " IDS("genre","ambient")},
    {"(" HAS("genre","ambient") " AND " HAS("keyword","watery") ") OR (" HAS("genre","rock") " AND " HAS("keyword","crunchy") ")", NULL, NULL,
     "SELECT id FROM (" IDS("genre","ambient") " INTERSECT " IDS("keyword","watery") ") UNION SELECT id FROM (" IDS("genre","rock") " INTERSECT " IDS("keyword","crunchy") ")"},
    {HAS("instrument","bass") " AND " HAS("instrument","keys"), "instrument", "bass",
     IDS("instrument","bass") " INTERSECT " IDS("instrument","keys")},
    {HAS("genre","ambient") " AND " HAS("keyword","watery") " AND " HAS("keyword","airy"), "keyword", "airy",
     IDS("genre","ambient") " INTERSECT " IDS("keyword","watery") " INTERSECT " IDS("keyword","airy")},
    {HAS("instrument","bass") " AND " HAS("keyword","absent"), "keyword", "absent",
     IDS("instrument","bass") " INTERSECT " IDS("keyword","absent")},
};

static int matches(int test, int id)
{
    switch (test) {
    case 0: return id%4==0 && (id%3==0 || id%7==0);
    case 1: return (id%4==0 || id%5==0) && id%11==0;
    case 2: return (id%11==0 && id%13==0) || (id%2==0 && id%19==0);
    case 3: return id%4==0 && id%5==0;
    case 4: return id%11==0 && id%13==0 && id%17==0;
    case 5: return 0;
    default: return 0;
    }
}

static int yield_build(void *unused)
{ (void)unused; vTaskDelay(1); return 0; }

static int cancel_query(void *calls)
{ ++*(int *)calls; return 1; }

/* Cancellation is per query; it must not poison the next filter request. */
static int check_cancellation(sqlite3 *db)
{
    sqlite3_stmt *query=NULL;
    int rc=sqlite3_prepare_v2(db,
        "SELECT c.id FROM effect c WHERE " HAS("keyword","absent"),
        -1,&query,NULL);
    if(rc!=SQLITE_OK)return rc;
    int calls=0;
    sqlite3_progress_handler(db,ROWS<16?1:64,cancel_query,&calls);
    rc=sqlite3_step(query);
    sqlite3_progress_handler(db,0,NULL,NULL);
    int finalize_rc=sqlite3_finalize(query);
    printf("CANCEL calls=%d step_rc=%d finalize_rc=%d\n",calls,rc,finalize_rc);
    if(rc!=SQLITE_INTERRUPT || finalize_rc!=SQLITE_INTERRUPT || calls!=1)
        return SQLITE_ERROR;
    return SQLITE_OK;
}

static int populate(sqlite3 *db)
{
    sqlite3_progress_handler(db,4096,yield_build,NULL);
    int rc=sqlite3_exec(db,
        "CREATE TABLE effect(id INTEGER PRIMARY KEY,name TEXT,description TEXT);"
        "CREATE INDEX effect_name ON effect(name,id);"
        "CREATE INDEX effect_id_name ON effect(id,name);"
        "CREATE TABLE facet(axis TEXT,value TEXT,effect_id INTEGER,PRIMARY KEY(axis,value,effect_id)) WITHOUT ROWID;"
        "BEGIN;"
        "WITH RECURSIVE ids(id) AS (VALUES(1) UNION ALL SELECT id+1 FROM ids WHERE id<" STRINGIFY(ROWS) ")"
        " INSERT INTO effect SELECT id,printf('Effect %06d',(id-1)/256),"
        " 'Synthetic layered delay, modulation and tone shaping for a generated instrument collection.' FROM ids;"
        "INSERT INTO facet SELECT 'instrument','bass',id FROM effect WHERE id%4=0;"
        "INSERT INTO facet SELECT 'instrument','keys',id FROM effect WHERE id%5=0;"
        "INSERT INTO facet SELECT 'type','delay',id FROM effect WHERE id%3=0;"
        "INSERT INTO facet SELECT 'type','modulation',id FROM effect WHERE id%7=0;"
        "INSERT INTO facet SELECT 'genre','ambient',id FROM effect WHERE id%11=0;"
        "INSERT INTO facet SELECT 'genre','rock',id FROM effect WHERE id%2=0;"
        "INSERT INTO facet SELECT 'keyword','watery',id FROM effect WHERE id%13=0;"
        "INSERT INTO facet SELECT 'keyword','airy',id FROM effect WHERE id%17=0;"
        "INSERT INTO facet SELECT 'keyword','crunchy',id FROM effect WHERE id%19=0;"
        "CREATE TABLE facet_page(axis TEXT,value TEXT,name TEXT,effect_id INTEGER,PRIMARY KEY(axis,value,name,effect_id)) WITHOUT ROWID;"
        "INSERT INTO facet_page SELECT axis,value,name,effect_id FROM facet JOIN effect ON effect.id=facet.effect_id;"
        "COMMIT;",NULL,NULL,NULL);
    sqlite3_progress_handler(db,0,NULL,NULL);
    if(rc!=SQLITE_OK) printf("COMPOSED populate error=%d %s\n",rc,sqlite3_errmsg(db));
    return rc;
}

static int walk(sqlite3 *db,int test,int strategy,int repeat,int first_only,int after)
{
    long long build_start=esp_timer_get_time();
    char from[1024],predicate[2048],sql[4096];
    if(strategy==3)
        strcpy(from,"(SELECT effect_id AS id,name FROM facet_page f WHERE axis='keyword' AND value='watery'"
            " AND EXISTS(SELECT 1 FROM facet WHERE axis='genre' AND value='ambient' AND effect_id=f.effect_id)"
            " UNION SELECT effect_id AS id,name FROM facet_page f WHERE axis='keyword' AND value='crunchy'"
            " AND EXISTS(SELECT 1 FROM facet WHERE axis='genre' AND value='rock' AND effect_id=f.effect_id)) c");
    else if(strategy==1)
        snprintf(from,sizeof(from),"(SELECT effect_id AS id,name FROM facet_page WHERE axis='%s' AND value='%s') c",cases[test].axis,cases[test].value);
    else if(strategy==2)strcpy(from,"effect c NOT INDEXED");
    else if(strategy==4)strcpy(from,"effect c INDEXED BY effect_id_name");
    else strcpy(from,"effect c");
    if(strategy==3)strcpy(predicate,"1");
    else if(strategy==2 || strategy==4)snprintf(predicate,sizeof(predicate),"c.id IN (%s)",cases[test].ids);
    else snprintf(predicate,sizeof(predicate),"%s",cases[test].predicate);
    snprintf(sql,sizeof(sql),"SELECT c.id,c.name FROM %s WHERE (c.name,c.id)>(?,?) AND (%s) ORDER BY c.name,c.id LIMIT 50",from,predicate);
    if(strategy==5)
        strcpy(sql,"SELECT effect_id AS id,name FROM facet_page f WHERE axis='keyword' AND value='watery'"
            " AND (f.name,f.effect_id)>(?1,?2)"
            " AND EXISTS(SELECT 1 FROM facet WHERE axis='genre' AND value='ambient' AND effect_id=f.effect_id)"
            " UNION SELECT effect_id AS id,name FROM facet_page f WHERE axis='keyword' AND value='crunchy'"
            " AND (f.name,f.effect_id)>(?1,?2)"
            " AND EXISTS(SELECT 1 FROM facet WHERE axis='genre' AND value='rock' AND effect_id=f.effect_id)"
            " ORDER BY name,id LIMIT 50");
    sqlite3_stmt *query=NULL;
    long long prepare_start=esp_timer_get_time();
    long long build_us=prepare_start-build_start;
    int rc=sqlite3_prepare_v2(db,sql,-1,&query,NULL);
    long long prepare_us=esp_timer_get_time()-prepare_start;
    if(rc!=SQLITE_OK) return rc;
    probe_read_reset();
    int last=after,expected=after,total=0,pages=0;
    int first_ids[50];
    long long first_us=0,max_us=0,step_us=0;
    long long bind_us=0,reset_us=0;
    int nav_rows=0;
    for(;;) {
        long long bind_start=esp_timer_get_time();
        char cursor[32];snprintf(cursor,sizeof(cursor),"Effect %06d",last?(last-1)/256:0);
        sqlite3_bind_text(query,1,cursor,-1,SQLITE_TRANSIENT);
        sqlite3_bind_int(query,2,last);
        if(first_only)bind_us=esp_timer_get_time()-bind_start;
        int rows=0;long long start=esp_timer_get_time();
        while((rc=sqlite3_step(query))==SQLITE_ROW) {
            do {expected++;} while(expected<=ROWS && !matches(test,expected));
            char name[32];snprintf(name,sizeof(name),"Effect %06d",(expected-1)/256);
            last=sqlite3_column_int(query,0);
            if(expected>ROWS || last!=expected || strcmp((const char *)sqlite3_column_text(query,1),name)) {
                rc=SQLITE_CORRUPT;goto done;
            }
            if(pages==0)first_ids[rows]=last;
            rows++;total++;
        }
        long long elapsed=esp_timer_get_time()-start;
        if(pages==0) {first_us=elapsed;probe_read_report(test,strategy,repeat);}
        if(elapsed>max_us) max_us=elapsed;
        step_us+=elapsed;
        if(rc!=SQLITE_DONE)goto done;
        long long reset_start=esp_timer_get_time();
        sqlite3_reset(query);
        if(first_only)reset_us=esp_timer_get_time()-reset_start;
        if(first_only) {
            nav_rows=rows;
            /* Verify exhaustion for short pages; full pages are verified prefixes. */
            if(rows<50) {
                do {expected++;} while(expected<=ROWS && !matches(test,expected));
                if(expected<=ROWS) {rc=SQLITE_CORRUPT;goto done;}
            }
            rc=SQLITE_OK;
            printf("NAV case=%d strategy=%d visit=%d after=%d rows=%d us=%lld memory=%lld rc=%d\n",
                test,strategy,repeat,after,rows,elapsed,(long long)sqlite3_memory_used(),rc);
            goto done;
        }
        if(pages==0) {
            /* Repeat only page one before any full-walk cache warming. */
            probe_read_reset();int hot_rows=0;
            start=esp_timer_get_time();
            while((rc=sqlite3_step(query))==SQLITE_ROW) {
                if(hot_rows>=rows || sqlite3_column_int(query,0)!=first_ids[hot_rows]) {rc=SQLITE_CORRUPT;goto done;}
                char name[32];snprintf(name,sizeof(name),"Effect %06d",(first_ids[hot_rows]-1)/256);
                if(strcmp((const char *)sqlite3_column_text(query,1),name)) {rc=SQLITE_CORRUPT;goto done;}
                hot_rows++;
            }
            elapsed=esp_timer_get_time()-start;
            probe_read_report(test,strategy,repeat+2);
            printf("HOTFIRST case=%d strategy=%d repeat=%d rows=%d us=%lld\n",test,strategy,repeat,hot_rows,elapsed);
            if(rc!=SQLITE_DONE || hot_rows!=rows) {rc=SQLITE_CORRUPT;goto done;}
            sqlite3_reset(query);
        }
        if(!rows)break;
        pages++;vTaskDelay(1);
    }
    do {expected++;} while(expected<=ROWS && !matches(test,expected));
    rc=expected>ROWS?SQLITE_OK:SQLITE_CORRUPT;
    printf("COMPOSED case=%d strategy=%d repeat=%d rows=%d pages=%d first_us=%lld max_us=%lld step_us=%lld memory=%lld rc=%d\n",
        test,strategy,repeat,total,pages,first_us,max_us,step_us,(long long)sqlite3_memory_used(),rc);
done:
    {
        long long finalize_start=esp_timer_get_time();
        int finalize_rc=sqlite3_finalize(query);
        long long finalize_us=esp_timer_get_time()-finalize_start;
        if(rc==SQLITE_OK && finalize_rc!=SQLITE_OK)rc=finalize_rc;
        if(first_only && rc==SQLITE_OK)
            printf("PAGE case=%d strategy=%d visit=%d after=%d rows=%d query_us=%lld build_us=%lld prepare_us=%lld bind_us=%lld step_us=%lld reset_us=%lld finalize_us=%lld\n",
                test,strategy,repeat,after,nav_rows,
                build_us+prepare_us+bind_us+first_us+reset_us+finalize_us,
                build_us,prepare_us,bind_us,first_us,reset_us,finalize_us);
    }
    return rc;
}

int probe_composed(sqlite3 **db)
{
    int rc=populate(*db);
    if(rc!=SQLITE_OK)return rc;
    rc=probe_sd_publish(db);
    if(rc!=SQLITE_OK)return rc;
    for(int test=0;test<(int)(sizeof(cases)/sizeof(cases[0]));test++) {
        for(int strategy=0;strategy<=5;strategy++) {
            if(strategy==1 && !cases[test].axis)continue;
            if((strategy==3 || strategy==5) && test!=2)continue;
            rc=probe_sd_reopen(db);
            if(rc!=SQLITE_OK)return rc;
            rc=walk(*db,test,strategy,0,0,0);
            if(rc!=SQLITE_OK)return rc;
            rc=walk(*db,test,strategy,1,0,0);
            if(rc!=SQLITE_OK)return rc;
        }
    }
    /* One connection, bounded cache, no immediate duplicate-page warming. */
    rc=sqlite3_exec(*db,"PRAGMA cache_size=-256",NULL,NULL,NULL);
    if(rc!=SQLITE_OK)return rc;
    rc=sqlite3_db_release_memory(*db);
    if(rc!=SQLITE_OK)return rc;
    static const int order[]={0,2,1,4,3,5,2,0,4,1,5,3};
    for(int visit=0;visit<72;visit++) {
        int test=order[visit%12];
        int strategy=test==2?5:test==4?2:1;
        int after=0;
        if(visit>=36)after=(visit/12)%2?ROWS/2:(ROWS>256?ROWS-256:ROWS);
        rc=walk(*db,test,strategy,visit+4,1,after);
        if(rc!=SQLITE_OK)return rc;
        vTaskDelay(1);
    }
    rc=check_cancellation(*db);
    if(rc!=SQLITE_OK)return rc;
    /* Verify a complete new filter prefix/exhaustion after interruption. */
    rc=walk(*db,0,1,76,1,0);
    if(rc!=SQLITE_OK)return rc;
    return SQLITE_OK;
}
