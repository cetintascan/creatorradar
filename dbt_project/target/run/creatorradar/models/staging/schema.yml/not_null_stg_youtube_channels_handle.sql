
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select handle
from `creatorradar-tr`.`creatorradar`.`stg_youtube_channels`
where handle is null



  
  
      
    ) dbt_internal_test