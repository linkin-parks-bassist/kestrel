#include "sqlite3.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <string.h>

/* Probe-only memory construction and immutable SD reads; no production locking. */
int probe_open(sqlite3_vfs *,const char *,sqlite3_file *,int,int *);
int probe_access(sqlite3_vfs *,const char *,int,int *);
int probe_full_path(sqlite3_vfs *,const char *,int,char *);
int probe_file_size(void);
int probe_sd_start(void);
int probe_sd_publish(sqlite3 **);
int probe_sd_reopen(sqlite3 **);
int probe_sd_cleanup(void);
int probe_composed(sqlite3 **);
static int random_bytes(sqlite3_vfs *v, int n, char *out)
{ (void)v; memset(out, 0, n); return n; }
static int current_time(sqlite3_vfs *v, double *out)
{ (void)v; *out = 2440587.5; return SQLITE_OK; }
static sqlite3_vfs memory_parent = {
 .iVersion=1, .szOsFile=sizeof(sqlite3_file), .mxPathname=128,
 .zName="probe-readonly-sd", .xOpen=probe_open,.xAccess=probe_access,.xFullPathname=probe_full_path,
 .xRandomness=random_bytes, .xCurrentTime=current_time
};
int sqlite3_os_init(void) { memory_parent.szOsFile=probe_file_size();return sqlite3_vfs_register(&memory_parent, 1); }
int sqlite3_os_end(void) { return SQLITE_OK; }

static int yield_build(void *context) { (void)context;vTaskDelay(1);return 0; }
static int exec(sqlite3 *db, const char *sql)
{
 sqlite3_progress_handler(db,4096,yield_build,NULL);
 int rc=sqlite3_exec(db,sql,0,0,0);
 sqlite3_progress_handler(db,0,NULL,NULL);
 if(rc!=SQLITE_OK) printf("SQL error %d: %s\n",rc,sqlite3_errmsg(db));
 return rc;
}
void app_main(void)
{
 sqlite3 *db=0; sqlite3_stmt *insert=0, *query=0;
 puts("PROBE ready; send g to start");
 while(getchar()!='g') { clearerr(stdin);vTaskDelay(1); }
 if(probe_sd_start()!=0) { printf("PROBE mount failed\n");return; }
 int rc=sqlite3_open(":memory:",&db);
 if(rc!=SQLITE_OK) goto done;
#ifdef CONFIG_KT_PROBE_COMPOSED
 rc=probe_composed(&db);
 goto done;
#endif
 rc=exec(db,"CREATE TABLE effect(id INTEGER PRIMARY KEY,name TEXT);"
 "CREATE TABLE facet(axis TEXT,value TEXT,effect_id INTEGER,PRIMARY KEY(axis,value,effect_id)) WITHOUT ROWID;"
 "CREATE INDEX effect_name ON effect(name,id);BEGIN;");
 if(rc!=SQLITE_OK) goto done;
 rc=sqlite3_prepare_v2(db,"INSERT INTO effect VALUES(?,?)",-1,&insert,0);
 if(rc!=SQLITE_OK) goto done;
 for(int i=1;i<=100000;i++) {
  char name[32]; snprintf(name,sizeof(name),"Effect %06d",(i-1)/256);
  sqlite3_bind_int(insert,1,i); sqlite3_bind_text(insert,2,name,-1,SQLITE_TRANSIENT);
  rc=sqlite3_step(insert); if(rc!=SQLITE_DONE) goto done;
  sqlite3_reset(insert);
  if(i%256==0) vTaskDelay(1);
 }
 sqlite3_finalize(insert); insert=0;
 rc=exec(db,"INSERT INTO facet SELECT 'instrument',CASE WHEN id%4=0 THEN 'bass' ELSE 'keys' END,id FROM effect;"
 "CREATE TABLE facet_page(axis TEXT,value TEXT,name TEXT,effect_id INTEGER,PRIMARY KEY(axis,value,name,effect_id)) WITHOUT ROWID;"
 "INSERT INTO facet_page SELECT axis,value,name,effect_id FROM facet JOIN effect ON effect.id=facet.effect_id;COMMIT;");
 if(rc!=SQLITE_OK) goto done;
 rc=probe_sd_publish(&db);
 if(rc!=SQLITE_OK) goto done;
 const int cursor_ids[]={0,0,0,200,99800};
 for(int pass=0;pass<5;pass++) {
  if(pass<2) { rc=probe_sd_reopen(&db);if(rc!=SQLITE_OK)goto done; }
  rc=sqlite3_prepare_v2(db,"SELECT effect_id,name FROM facet_page WHERE axis='instrument' AND value=? AND (name,effect_id)>(?,?) ORDER BY name,effect_id LIMIT 50",-1,&query,0);
  if(rc!=SQLITE_OK)goto done;
  char cursor[32];snprintf(cursor,sizeof(cursor),"Effect %06d",cursor_ids[pass]?(cursor_ids[pass]-1)/256:0);
  sqlite3_bind_text(query,1,pass==0?"absent":"bass",-1,SQLITE_STATIC);
  sqlite3_bind_text(query,2,cursor,-1,SQLITE_TRANSIENT);sqlite3_bind_int(query,3,cursor_ids[pass]);
  int rows=0; long long start=esp_timer_get_time();
  while((rc=sqlite3_step(query))==SQLITE_ROW) {
   rows++;int expected=cursor_ids[pass]+rows*4;
   char name[32];snprintf(name,sizeof(name),"Effect %06d",(expected-1)/256);
   if(sqlite3_column_int(query,0)!=expected || strcmp((const char *)sqlite3_column_text(query,1),name)) { rc=SQLITE_CORRUPT; goto done; }
  }
  printf("COVERING pass=%d cursor=%d rows=%d us=%lld sqlite_memory=%lld\n",pass,cursor_ids[pass],rows,(long long)(esp_timer_get_time()-start),(long long)sqlite3_memory_used());
  if(rc!=SQLITE_DONE || rows!=(pass==0?0:50)) { rc=SQLITE_CORRUPT; goto done; }
  sqlite3_finalize(query);query=NULL;
 }
 rc=sqlite3_prepare_v2(db,"SELECT effect_id,name FROM facet_page WHERE axis='instrument' AND value='bass' AND (name,effect_id)>(?,?) ORDER BY name,effect_id LIMIT 50",-1,&query,0);
 if(rc!=SQLITE_OK)goto done;
 int total=0,pages=0,last_id=0;long long walk_start=esp_timer_get_time();
 for(;;) {
  char cursor[32];snprintf(cursor,sizeof(cursor),"Effect %06d",last_id?(last_id-1)/256:0);
  sqlite3_bind_text(query,1,cursor,-1,SQLITE_TRANSIENT);sqlite3_bind_int(query,2,last_id);
  int rows=0;
  while((rc=sqlite3_step(query))==SQLITE_ROW) {
   total++;rows++;int expected=total*4;
   char name[32];snprintf(name,sizeof(name),"Effect %06d",(expected-1)/256);
   last_id=sqlite3_column_int(query,0);
   if(last_id!=expected || strcmp((const char *)sqlite3_column_text(query,1),name)) { rc=SQLITE_CORRUPT;goto done; }
  }
  if(rc!=SQLITE_DONE){goto done;}
  sqlite3_reset(query);
  if(rows==0)break;
  pages++;vTaskDelay(1);
 }
 printf("WALK rows=%d pages=%d us=%lld\n",total,pages,(long long)(esp_timer_get_time()-walk_start));
 rc=(total==25000 && pages==500)?SQLITE_OK:SQLITE_CORRUPT;
done:
 sqlite3_finalize(insert); sqlite3_finalize(query); sqlite3_close(db);
 int cleanup=probe_sd_cleanup();
 printf("PROBE rc=%d cleanup=%d stack_free=%u\n",rc,cleanup,(unsigned)uxTaskGetStackHighWaterMark(NULL));
}
