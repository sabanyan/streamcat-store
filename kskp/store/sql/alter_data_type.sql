/* type列をtyp1列に名称変更する */
alter table data rename column "type" to type1;

/* type列を新規追加する */
alter table data add column "type" text;

/* type1列からtype列へ値をコピーする */
update data set type = type1;

/* data_type型をtype1列と共に削除する */
drop type data_type cascade;

/* data_typeを新規作成する */
create type data_type as enum('folder','project','awss3','rfolder','database','flow','frame','trash','command');

/* type列をdata_type型にキャストする */
alter table data alter column "type" type data_type  using cast("type" as data_type) ;

