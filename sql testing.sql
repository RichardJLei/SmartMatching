select * from parsing_results order by updated_at desc

select * from confirmation_files


INSERT INTO confirmation_files (file_name, file_path)
VALUES ('bank swap confo 1.pdf', 'received_files/');

select parsing_results.parsed_json->'content'->'parsed_result'->'parsed_content',* from parsing_results,confirmation_files 
where confirmation_files.file_name='DealConfirmationAdvice - fx swap.pdf'
and parsing_results.file_id=confirmation_files.file_id
order by parsing_results.updated_at desc 