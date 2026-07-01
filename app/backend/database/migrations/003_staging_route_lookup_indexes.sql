CREATE INDEX IF NOT EXISTS idx_staging_train_stops_station_train_sequence
ON staging_train_stops (station_code, train_number, stop_sequence);

CREATE INDEX IF NOT EXISTS idx_staging_train_stops_train_sequence_station
ON staging_train_stops (train_number, stop_sequence, station_code);

CREATE INDEX IF NOT EXISTS idx_staging_train_stops_station_sequence
ON staging_train_stops (station_code, stop_sequence);

CREATE INDEX IF NOT EXISTS idx_staging_train_stops_train_station_sequence
ON staging_train_stops (train_number, station_code, stop_sequence);
