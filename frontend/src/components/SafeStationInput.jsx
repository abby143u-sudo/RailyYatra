import {
  useId,
  useRef,
  useState,
} from "react";
import { API_BASE } from "../config/api.js";

function stationCode(station) {
  return String(
    station?.station_code ||
      station?.code ||
      station?.id ||
      "",
  )
    .trim()
    .toUpperCase();
}

function stationName(station) {
  return String(
    station?.station_name ||
      station?.name ||
      station?.label ||
      "Station name unavailable",
  ).trim();
}

export default function SafeStationInput({
  label,
  value,
  onChange,
  placeholder,
}) {
  const generatedId = useId().replaceAll(":", "");
  const inputId = `station-input-${generatedId}`;
  const listboxId = `${inputId}-listbox`;
  const hintId = `${inputId}-hint`;

  const requestSequence = useRef(0);

  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);

  const expanded = stations.length > 0;
  const hintText = loading
    ? "Loading stations..."
    : message;

  function closeSuggestions() {
    setStations([]);
    setActiveIndex(-1);
  }

  async function loadStations(nextValue) {
    const query = String(nextValue || "")
      .trim()
      .toUpperCase();

    onChange(query);
    setActiveIndex(-1);

    requestSequence.current += 1;
    const currentRequest = requestSequence.current;

    if (query.length < 2) {
      setStations([]);
      setLoading(false);
      setMessage("");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const params = new URLSearchParams({
        q: query,
        limit: "8",
      });

      const response = await fetch(
        `${API_BASE}/staging/stations?${params.toString()}`,
      );

      if (currentRequest !== requestSequence.current) {
        return;
      }

      if (!response.ok) {
        setStations([]);
        setMessage("");
        return;
      }

      const data = await response.json();

      if (currentRequest !== requestSequence.current) {
        return;
      }

      const safeStations = Array.isArray(data?.stations)
        ? data.stations
        : [];

      setStations(safeStations);
      setMessage(
        safeStations.length
          ? ""
          : "No station found.",
      );
    } catch {
      if (currentRequest === requestSequence.current) {
        setStations([]);
        setMessage("");
      }
    } finally {
      if (currentRequest === requestSequence.current) {
        setLoading(false);
      }
    }
  }

  function chooseStation(station) {
    const code = stationCode(station);

    if (!code) {
      return;
    }

    onChange(code);
    setMessage("");
    closeSuggestions();
  }

  function handleKeyDown(event) {
    if (event.key === "Escape") {
      closeSuggestions();
      return;
    }

    if (!stations.length) {
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();

      setActiveIndex((current) =>
        current < stations.length - 1
          ? current + 1
          : 0,
      );

      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();

      setActiveIndex((current) =>
        current > 0
          ? current - 1
          : stations.length - 1,
      );

      return;
    }

    if (
      event.key === "Enter" &&
      activeIndex >= 0
    ) {
      event.preventDefault();
      chooseStation(stations[activeIndex]);
    }
  }

  return (
    <div className="field safe-station-input">
      <label htmlFor={inputId}>
        {label}
      </label>

      <input
        id={inputId}
        role="combobox"
        value={value}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck="false"
        aria-autocomplete="list"
        aria-haspopup="listbox"
        aria-expanded={expanded}
        aria-controls={
          expanded ? listboxId : undefined
        }
        aria-activedescendant={
          activeIndex >= 0
            ? `${listboxId}-option-${activeIndex}`
            : undefined
        }
        aria-describedby={
          hintText ? hintId : undefined
        }
        onChange={(event) =>
          loadStations(event.target.value)
        }
        onKeyDown={handleKeyDown}
        onBlur={() =>
          window.setTimeout(
            closeSuggestions,
            160,
          )
        }
      />

      {hintText && (
        <p
          id={hintId}
          className="safe-station-input__hint"
          role="status"
          aria-live="polite"
        >
          {hintText}
        </p>
      )}

      {expanded && (
        <div
          id={listboxId}
          className="safe-station-input__panel"
          role="listbox"
          aria-label={`${label} station suggestions`}
        >
          {stations.map((station, index) => {
            const code = stationCode(station);
            const name = stationName(station);
            const selected = index === activeIndex;

            return (
              <button
                id={`${listboxId}-option-${index}`}
                type="button"
                role="option"
                aria-selected={selected}
                tabIndex={-1}
                key={`${code || "station"}-${index}`}
                onMouseEnter={() =>
                  setActiveIndex(index)
                }
                onMouseDown={(event) =>
                  event.preventDefault()
                }
                onClick={() =>
                  chooseStation(station)
                }
              >
                <strong>{code || "N/A"}</strong>
                <span>{name}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
