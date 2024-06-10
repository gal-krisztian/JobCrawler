-- Create a function that returns 0 or 1 if a column is already exist in a table (Boolean datatype when in XE?).
create or replace function is_exists_column(
    p_owner varchar2,
    p_table_name varchar2,
    p_column_name varchar2)

return pls_integer

authid current_user

is

l_is_exists pls_integer;
l_owner        all_tab_columns.owner%type           :=  upper(p_owner);
l_table_name   all_tab_columns.table_name%type      :=  upper(p_table_name);
l_column_name  all_tab_columns.column_name%type     :=  upper(p_column_name);

begin

select case when count(*) > 0 
    then 1 
    else 0 end into l_is_exists 
    from all_tab_columns c 
    where c.owner = is_exists_column.l_owner 
    and c.table_name = is_exists_column.l_table_name 
    and c.column_name = is_exists_column.l_column_name;

return l_is_exists;

end is_exists_column;
/

-- Grant the EXECUTE privilege on the function to the PUBLIC role to enable access for all users.
grant execute on is_exists_column to public;
/

-- Create a function that returns 0 or 1 if a table is already exist in the database
create or replace function is_exists_table(
    p_owner varchar2,
    p_table_name varchar2)
    
return number

authid current_user

is
l_is_exists     number;
l_owner         all_tables.owner%type       :=  upper(p_owner);
l_table_name    all_tables.table_name%type  :=  upper(p_table_name);

begin

select case when count(*) > 0 
        then 1 
        else 0 end into is_exists_table.l_is_exists 
        from all_tables t 
        where t.owner = is_exists_table.l_owner 
        and t.table_name = is_exists_table.l_table_name;

return l_is_exists;

end is_exists_table;
/

-- Grant the EXECUTE privilege on the function to the PUBLIC role to enable access for all users.
grant execute on is_exists_table to public;
/

-- grant privilege for testing purposes.
grant execute on is_exists_column to jobscrape;
/

-- grant privilege for testing purposes.
grant execute on is_exists_table to jobscrape;
/
