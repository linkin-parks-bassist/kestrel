#include "sqlite3.h"
#include "esp_vfs_fat.h"
#include "sdmmc_cmd.h"
#include "driver/sdmmc_host.h"
#include "sd_pwr_ctrl_by_on_chip_ldo.h"
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include "esp_timer.h"
#include "sdkconfig.h"
#include "esp_attr.h"
#include "sd_protocol_defs.h"

#define FIXTURE "/sdcard/KTPROBE.DB"
typedef struct { sqlite3_file base; FILE *stream; int fd; } probe_file;
static int created;
static long long reads,read_bytes,read_us;
static long long single_reads,multiple_reads,sd_bytes;
static esp_err_t (*transaction)(int,sdmmc_command_t *);
static esp_err_t probe_transaction(int slot,sdmmc_command_t *cmd)
{
 if(cmd->opcode==MMC_READ_BLOCK_SINGLE)single_reads++;
 if(cmd->opcode==MMC_READ_BLOCK_MULTIPLE)multiple_reads++;
 if(cmd->opcode==MMC_READ_BLOCK_SINGLE || cmd->opcode==MMC_READ_BLOCK_MULTIPLE)sd_bytes+=cmd->datalen;
 return transaction(slot,cmd);
}
#if CONFIG_KT_PROBE_DMA_READ
static DRAM_ATTR unsigned char dma_read[4096] __attribute__((aligned(64)));
#endif
void probe_read_reset(void) {reads=read_bytes=read_us=single_reads=multiple_reads=sd_bytes=0;}
void probe_read_report(int test,int strategy,int repeat)
{printf("IO case=%d strategy=%d repeat=%d reads=%lld bytes=%lld us=%lld single=%lld multiple=%lld sd_bytes=%lld\n",test,strategy,repeat,reads,read_bytes,read_us,single_reads,multiple_reads,sd_bytes);}
static int close_file(sqlite3_file *f)
{
 probe_file *p=(probe_file *)f;
#if CONFIG_KT_PROBE_RAW_READ
 return close(p->fd)==0?SQLITE_OK:SQLITE_IOERR_CLOSE;
#else
 return fclose(p->stream)==0?SQLITE_OK:SQLITE_IOERR_CLOSE;
#endif
}
static int read_file(sqlite3_file *f, void *out, int n, sqlite3_int64 offset)
{
 long long start=esp_timer_get_time();reads++;read_bytes+=n;
#if CONFIG_KT_PROBE_RAW_READ
 int fd=((probe_file *)f)->fd;
 if(lseek(fd,(off_t)offset,SEEK_SET)<0) {read_us+=esp_timer_get_time()-start;return SQLITE_IOERR_SEEK;}
#if CONFIG_KT_PROBE_DMA_READ
 ssize_t got=0;
 while(got<n) {
  size_t count=n-got;if(count>sizeof(dma_read))count=sizeof(dma_read);
  ssize_t part=read(fd,dma_read,count);
  if(part<0) {read_us+=esp_timer_get_time()-start;return SQLITE_IOERR_READ;}
  if(part==0)break;
  memcpy((char *)out+got,dma_read,part);got+=part;
 }
#else
 ssize_t got=read(fd,out,n);
#endif
 read_us+=esp_timer_get_time()-start;
 if(got<0)return SQLITE_IOERR_READ;
 if(got==n)return SQLITE_OK;
 memset((char *)out+got,0,n-got);
 return SQLITE_IOERR_SHORT_READ;
#else
 FILE *s=((probe_file *)f)->stream;
 if(fseek(s,(long)offset,SEEK_SET)) {read_us+=esp_timer_get_time()-start;return SQLITE_IOERR_SEEK;}
 size_t got=fread(out,1,n,s);
 read_us+=esp_timer_get_time()-start;
 if(got==(size_t)n) return SQLITE_OK;
 memset((char *)out+got,0,n-got);
 return ferror(s)?SQLITE_IOERR_READ:SQLITE_IOERR_SHORT_READ;
#endif
}
static int write_file(sqlite3_file *f,const void *b,int n,sqlite3_int64 o)
{ (void)f;(void)b;(void)n;(void)o;return SQLITE_READONLY; }
static int truncate_file(sqlite3_file *f,sqlite3_int64 n)
{ (void)f;(void)n;return SQLITE_READONLY; }
static int sync_file(sqlite3_file *f,int flags)
{ (void)f;(void)flags;return SQLITE_OK; }
static int size_file(sqlite3_file *f,sqlite3_int64 *size)
{
 probe_file *p=(probe_file *)f;
#if CONFIG_KT_PROBE_RAW_READ
 int fd=p->fd;
#else
 int fd=fileno(p->stream);
#endif
 struct stat st;if(fstat(fd,&st))return SQLITE_IOERR_FSTAT;*size=st.st_size;return SQLITE_OK;
}
static int lock_file(sqlite3_file *f,int lock)
{ (void)f;(void)lock;return SQLITE_OK; }
static int reserved_file(sqlite3_file *f,int *out)
{ (void)f;*out=0;return SQLITE_OK; }
static int control_file(sqlite3_file *f,int op,void *out)
{ (void)f;(void)op;(void)out;return SQLITE_NOTFOUND; }
static int sector_file(sqlite3_file *f) { (void)f;return 512; }
static int characteristics_file(sqlite3_file *f) { (void)f;return SQLITE_IOCAP_IMMUTABLE; }
static const sqlite3_io_methods methods={
 .iVersion=1,.xClose=close_file,.xRead=read_file,.xWrite=write_file,
 .xTruncate=truncate_file,.xSync=sync_file,.xFileSize=size_file,
 .xLock=lock_file,.xUnlock=lock_file,.xCheckReservedLock=reserved_file,
 .xFileControl=control_file,.xSectorSize=sector_file,.xDeviceCharacteristics=characteristics_file
};
int probe_open(sqlite3_vfs *v,const char *name,sqlite3_file *file,int flags,int *out)
{
 (void)v;
 if(!created || !name || strcmp(name,FIXTURE) || !(flags&SQLITE_OPEN_READONLY)) return SQLITE_CANTOPEN;
 probe_file *f=(probe_file *)file;
#if CONFIG_KT_PROBE_RAW_READ
 f->fd=open(name,O_RDONLY);if(f->fd<0)return SQLITE_CANTOPEN;
#else
 f->stream=fopen(name,"rb"); if(!f->stream)return SQLITE_CANTOPEN;
#endif
 f->base.pMethods=&methods; if(out)*out=SQLITE_OPEN_READONLY;return SQLITE_OK;
}
int probe_access(sqlite3_vfs *v,const char *n,int flags,int *out)
{ (void)v;(void)flags;*out=access(n,F_OK)==0;return SQLITE_OK; }
int probe_full_path(sqlite3_vfs *v,const char *n,int size,char *out)
{ (void)v;return snprintf(out,size,"%s",n)<size?SQLITE_OK:SQLITE_CANTOPEN; }
int probe_sd_start(void)
{
#if CONFIG_KT_PROBE_DMA_READ
 printf("SD read_path=lseek/read-aligned-internal\n");
#elif CONFIG_KT_PROBE_RAW_READ
 printf("SD read_path=lseek/read\n");
#else
 printf("SD read_path=fseek/fread\n");
#endif
 sd_pwr_ctrl_ldo_config_t cfg={.ldo_chan_id=4};
 sd_pwr_ctrl_handle_t power=NULL;
 esp_err_t rc=sd_pwr_ctrl_new_on_chip_ldo(&cfg,&power);
 if(rc!=ESP_OK)return rc;
 sd_pwr_ctrl_set_io_voltage(power,3300);
 sdmmc_host_t host=SDMMC_HOST_DEFAULT();host.pwr_ctrl_handle=power;
 transaction=host.do_transaction;host.do_transaction=probe_transaction;
 sdmmc_slot_config_t slot=SDMMC_SLOT_CONFIG_DEFAULT();
 slot.width=4;slot.clk=43;slot.cmd=44;slot.d0=39;slot.d1=40;slot.d2=41;slot.d3=42;
 slot.flags|=SDMMC_SLOT_FLAG_INTERNAL_PULLUP;
 esp_vfs_fat_sdmmc_mount_config_t mount={.format_if_mount_failed=false,.max_files=5,.allocation_unit_size=16384};
 sdmmc_card_t *card=NULL;
 return esp_vfs_fat_sdmmc_mount("/sdcard",&host,&slot,&mount,&card);
}
int probe_sd_reopen(sqlite3 **db)
{
 int rc=sqlite3_close(*db);if(rc!=SQLITE_OK)return rc;*db=NULL;
 return sqlite3_open_v2("file:" FIXTURE "?immutable=1",db,SQLITE_OPEN_READONLY|SQLITE_OPEN_URI,NULL);
}
int probe_sd_publish(sqlite3 **db)
{
 sqlite3_int64 bytes=0;unsigned char *data=sqlite3_serialize(*db,"main",&bytes,0);
 if(!data)return SQLITE_NOMEM;
 int fd=open(FIXTURE,O_WRONLY|O_CREAT|O_EXCL,0600);
 if(fd<0){printf("SD fixture create failed errno=%d\n",errno);sqlite3_free(data);return SQLITE_CANTOPEN;}
 created=1;
 size_t written=0;
 while(written<(size_t)bytes) {
  size_t chunk=(size_t)bytes-written;if(chunk>65536)chunk=65536;
  ssize_t n=write(fd,data+written,chunk);if(n<=0)break;
  written+=(size_t)n;
 }
 sqlite3_free(data);
 int synced=fsync(fd);int closed=close(fd);
 if(written!=(size_t)bytes || synced || closed)return SQLITE_IOERR_WRITE;
 printf("SD fixture bytes=%lld\n",(long long)bytes);
 return probe_sd_reopen(db);
}
int probe_sd_cleanup(void)
{ return created?unlink(FIXTURE):0; }
int probe_file_size(void) { return sizeof(probe_file); }
