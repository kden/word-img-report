
select title_instance_id, isbn, title, publisher, title_source, lowercase, round(size_bytes/1048576,1) as MB, count(img_id) as image_count
from img 
where lowercase in ('equation','image','images','img','inline','math','jpg','alt') and size_bytes > 1000 and size_bytes is not null
and source_format='EPUB2'
group by title_instance_id, isbn, title,  publisher, title_source, lowercase, size_bytes
having count(img_id) > 10
order by MB asc