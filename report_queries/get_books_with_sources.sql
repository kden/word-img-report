
select title_instance_id, isbn, title, publisher, title_source, round(size_bytes/1048576,1) as MB, count(img_id) as image_count
from img 
where (alt='' or alt is null) and size_bytes > 1000 and size_bytes is not null and source_format='EPUB2'
group by title_instance_id, isbn, title, publisher, title_source, size_bytes
having count(img_id) > 10
order by MB asc