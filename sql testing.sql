

select processing_status,* from confirmation_files

select * from matching_units

select latest,* from parsing_results

--delete from parsing_results


select  parsing_results.parsed_json->'content'->'parsed_result'->'parsed_content',* from parsing_results,confirmation_files 
where confirmation_files.file_name='DealConfirmationAdvice - fx swap.pdf'
and parsing_results.file_id=confirmation_files.file_id
order by parsing_results.updated_at desc 


/*
INSERT INTO confirmation_files (file_name, file_path)
VALUES ('REKOSELEOS24327996801.pdf', 'received_files/');
INSERT INTO confirmation_files (file_name, file_path)
VALUES ('DealConfirmationAdvice.pdf', 'received_files/');
INSERT INTO confirmation_files (file_name, file_path)
VALUES ('DealConfirmationAdvice - fx swap.pdf', 'received_files/');
INSERT INTO confirmation_files (file_name, file_path)
VALUES ('bank swap confo 1.pdf', 'received_files/');
INSERT INTO confirmation_files (file_name, file_path)
VALUES ('bank swap confo 2.pdf', 'received_files/');

*/