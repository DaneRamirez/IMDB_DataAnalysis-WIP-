--If you wanna recreate my data analysis here are the views that I have used:--

--Actor ratings--
CREATE MATERIALIZED VIEW mv_actor_ratings AS
WITH avg_votes AS (
  SELECT AVG(numVotes) AS global_avg_votes
  FROM title_ratings
)
SELECT 
  nb.nconst,
  nb.primaryName AS actor_name,
  COUNT(DISTINCT tr.tconst) AS num_movies,
  AVG(tr.averageRating) AS avg_rating,
  SUM(tr.numVotes) AS total_votes
FROM name_basics nb
JOIN title_principals tp ON nb.nconst = tp.nconst
JOIN title_ratings tr ON tp.tconst = tr.tconst
CROSS JOIN avg_votes
WHERE 
  tp.category IN ('actor', 'actress')
  AND tr.numVotes >= avg_votes.global_avg_votes 
GROUP BY nb.nconst, nb.primaryName
HAVING COUNT(DISTINCT tr.tconst) >= 5
ORDER BY avg_rating DESC;

--Countries top ratings--
CREATE MATERIALIZED VIEW mv_country_ratings AS
WITH avg_votes AS (
  SELECT AVG(numVotes) AS global_avg_votes
  FROM title_ratings
)
SELECT 
  ta.region AS country,
  COUNT(DISTINCT ta.titleId) AS num_titles,
  AVG(tr.averageRating) AS avg_rating,
  SUM(tr.numVotes) AS total_votes
FROM title_akas ta
JOIN title_ratings tr ON ta.titleId = tr.tconst
CROSS JOIN avg_votes
WHERE 
  ta.region IS NOT NULL
  AND tr.numVotes >= avg_votes.global_avg_votes  
GROUP BY ta.region
ORDER BY avg_rating DESC;


--Directors and ratings--
CREATE MATERIALIZED VIEW mv_director_ratings AS
WITH avg_votes AS (
  SELECT AVG(numVotes) AS global_avg_votes
  FROM title_ratings
)
SELECT 
  nb.nconst,
  nb.primaryName AS director_name,
  COUNT(DISTINCT tr.tconst) AS num_movies,
  AVG(tr.averageRating) AS avg_rating,
  SUM(tr.numVotes) AS total_votes
FROM name_basics nb
JOIN title_principals tp ON nb.nconst = tp.nconst
JOIN title_ratings tr ON tp.tconst = tr.tconst
CROSS JOIN avg_votes
WHERE 
  tp.category = 'director'
  AND tr.numVotes >= avg_votes.global_avg_votes  
GROUP BY nb.nconst, nb.primaryName
HAVING COUNT(DISTINCT tr.tconst) >= 3
ORDER BY avg_rating DESC;


--Original title vs ratings--
CREATE MATERIALIZED VIEW mv_original_title_ratings AS
WITH avg_votes AS (
  SELECT AVG(numVotes) AS global_avg_votes
  FROM title_ratings
)
SELECT 
  ta.isOriginalTitle,
  COUNT(DISTINCT ta.titleId) AS num_titles,
  AVG(tr.averageRating) AS avg_rating,
  SUM(tr.numVotes) AS total_votes
FROM title_akas ta
JOIN title_ratings tr ON ta.titleId = tr.tconst
CROSS JOIN avg_votes
WHERE tr.numVotes >= avg_votes.global_avg_votes  -- Filter titles with votes ≥ average
GROUP BY ta.isOriginalTitle;

--Top rated movies worldwide--
CREATE MATERIALIZED VIEW mv_top_global_ratings AS
WITH avg_votes AS (
  SELECT AVG(numVotes) AS global_avg_votes
  FROM title_ratings
)
SELECT 
  tb.tconst,
  tb.primaryTitle,
  tb.startYear,
  tb.genres,
  tr.averageRating,
  tr.numVotes
FROM title_basics tb
JOIN title_ratings tr ON tb.tconst = tr.tconst
CROSS JOIN avg_votes
WHERE 
  tb.titleType = 'movie'
  AND tr.numVotes >= avg_votes.global_avg_votes  -- Filter titles with votes ≥ average
ORDER BY tr.averageRating DESC
LIMIT 100;



--Ratings by genre--
CREATE MATERIALIZED VIEW mv_genre_ratings AS
WITH avg_votes AS (
  SELECT AVG(numVotes) AS global_avg_votes
  FROM title_ratings
)
SELECT 
  genre,
  COUNT(DISTINCT tb.tconst) AS num_titles,
  AVG(tr.averageRating) AS avg_rating,
  SUM(tr.numVotes) AS total_votes
FROM (
  SELECT tconst, unnest(genres) AS genre 
  FROM title_basics
) tb
JOIN title_ratings tr ON tb.tconst = tr.tconst
CROSS JOIN avg_votes
WHERE tr.numVotes >= avg_votes.global_avg_votes  -- Filter titles with votes ≥ average
GROUP BY genre
ORDER BY avg_rating DESC;

