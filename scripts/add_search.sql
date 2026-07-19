ALTER TABLE films ADD COLUMN IF NOT EXISTS search_vector tsvector 
  GENERATED ALWAYS AS (
    to_tsvector('english', coalesce(title,'') || ' ' || coalesce(synopsis,''))
  ) STORED;

CREATE INDEX IF NOT EXISTS films_search_idx ON films USING GIN(search_vector);

ALTER TABLE persons ADD COLUMN IF NOT EXISTS search_vector tsvector 
  GENERATED ALWAYS AS (
    to_tsvector('english', coalesce(name,''))
  ) STORED;

CREATE INDEX IF NOT EXISTS persons_search_idx ON persons USING GIN(search_vector);
