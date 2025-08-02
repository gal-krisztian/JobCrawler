-- Create user.
create user jobcrawler identified by <password>;
/

-- Grant privilege to be able to connect to database.
grant create session to jobcrawler;
/

-- Grant privilege to be able to create functions, procedures or packages.
grant create procedure to jobcrawler;
/

-- Grant privilege to be able to create table
grant create table to jobcrawler;

-- Grant unlimited tablespace to be able to insert into tables
grant unlimited tablespace to jobcrawler;

-- Grant privilege to be able to create triggers
grant create trigger to jobcrawler;

-- Grant privilege to be able to create sequences
grant create sequence to jobcrawler;