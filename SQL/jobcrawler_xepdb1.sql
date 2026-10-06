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

-- create a sequence to generate identification numbers for companys
CREATE SEQUENCE scrape_company_seq
  START WITH 1
  INCREMENT BY 1
  NOCACHE
  NOCYCLE;
/

-- create scrape_company table
CREATE TABLE scrape_company (
    id VARCHAR2(11) PRIMARY KEY,
    tnd DATE,
    company_name VARCHAR2(150),
    company_full_address VARCHAR2(500),
    country VARCHAR2(50),
    country_code VARCHAR2(2),
    state VARCHAR2(100),
    county VARCHAR2(50),
    city VARCHAR2(50),
    postcode VARCHAR2(20),
    district VARCHAR2(75),
    street VARCHAR2(50),
    housenumber VARCHAR2(10)
);
/

-- create trigger to generate identification numbers in scrape_company
CREATE OR REPLACE TRIGGER scrape_company_trg
BEFORE INSERT ON scrape_company
FOR EACH ROW
BEGIN
  IF :NEW.id IS NULL THEN
    SELECT 'COMP' || LPAD(scrape_company_seq.NEXTVAL, 7, '0')
    INTO :NEW.id
    FROM dual;
  END IF;
END;
/

-- create scrape_job table
CREATE TABLE scrape_job (
    id VARCHAR2(8),
    tnd DATE,
    source VARCHAR2(20),
    status VARCHAR2(1),
    status_from DATE,
    status_to DATE,
    url VARCHAR2(300),
    position VARCHAR2(200),
    company_id VARCHAR2(11),
	employment_type VARCHAR2(50),
    category1 VARCHAR2(100),
    category2 VARCHAR2(100),
    min_salary_by_hour NUMBER(10, 2),
    max_salary_by_hour NUMBER(10, 2),
    currency VARCHAR2(10),
	CONSTRAINT pk_scrape_job PRIMARY KEY (id, source),
    CONSTRAINT fk_scrape_job_company
        FOREIGN KEY (company_id)
        REFERENCES scrape_company(id)
);

