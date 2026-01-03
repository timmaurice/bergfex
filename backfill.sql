INSERT INTO `bergfex-481612.bergfex_data.dim_resorts` (resort_id, resort_name, country, area_url, region, elevation_valley, elevation_mountain)
SELECT DISTINCT
    TO_HEX(MD5(area_url)) as resort_id,
    resort_name,
    country,
    area_url,
    CAST(NULL as STRING) as region, -- Legacy data might not have this
    CAST(NULL as INT64) as elevation_valley,
    CAST(NULL as INT64) as elevation_mountain
FROM `bergfex-481612.bergfex_data.snow_reports`
WHERE TO_HEX(MD5(area_url)) NOT IN (SELECT resort_id FROM `bergfex-481612.bergfex_data.dim_resorts`);

INSERT INTO `bergfex-481612.bergfex_data.fct_snow_measurements` (measurement_id, resort_id, date, timestamp, snow_valley, snow_mountain, new_snow, lifts_open, lifts_total, slopes_open_km, slopes_total_km, status, avalanche_warning, snow_condition)
SELECT
    CONCAT(TO_HEX(MD5(area_url)), "_", CAST(DATE(scraped_at) AS STRING)) as measurement_id,
    TO_HEX(MD5(area_url)) as resort_id,
    DATE(scraped_at) as date,
    scraped_at as timestamp,
    CAST(REGEXP_EXTRACT(snow_valley, r'\d+') AS INT64) as snow_valley,
    CAST(REGEXP_EXTRACT(snow_mountain, r'\d+') AS INT64) as snow_mountain,
    CAST(REGEXP_EXTRACT(new_snow, r'\d+') AS INT64) as new_snow,
    lifts_open_count as lifts_open,
    lifts_total_count as lifts_total,
    slopes_open_km,
    slopes_total_km,
    status,
    CAST(avalanche_warning AS INT64) as avalanche_warning, -- Might fail if mixed string/int in legacy, stick to safe cast
    snow_condition
FROM `bergfex-481612.bergfex_data.snow_reports`
WHERE CONCAT(TO_HEX(MD5(area_url)), "_", CAST(DATE(scraped_at) AS STRING)) NOT IN (SELECT measurement_id FROM `bergfex-481612.bergfex_data.fct_snow_measurements`);
