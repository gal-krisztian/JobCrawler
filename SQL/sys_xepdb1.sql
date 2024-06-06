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