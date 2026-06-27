
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select video_title
from `creatorradar-tr`.`creatorradar`.`stg_youtube_videos`
where video_title is null



  
  
      
    ) dbt_internal_test