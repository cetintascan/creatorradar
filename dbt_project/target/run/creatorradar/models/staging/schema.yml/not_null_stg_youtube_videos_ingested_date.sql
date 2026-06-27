
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select ingested_date
from `creatorradar-tr`.`creatorradar`.`stg_youtube_videos`
where ingested_date is null



  
  
      
    ) dbt_internal_test