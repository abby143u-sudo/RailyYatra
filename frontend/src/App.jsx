import { useMemo, useState, useEffect } from "react";
import "./App.css";
import PublicDemoFooter from "./components/PublicDemoFooter.jsx";
import { API_BASE } from "./config/api.js";
import Phase3StagingCard from "./components/Phase3StagingCard.jsx";
import Phase3DirectPreview from "./components/Phase3DirectPreview.jsx";
import Phase3RouteSearchPreview from "./components/Phase3RouteSearchPreview.jsx";
import Phase4RecommendationPreview from "./components/Phase4RecommendationPreview.jsx";
import Phase5ProductStatusPanel from "./components/Phase5ProductStatusPanel.jsx";
import Phase5BetaChecklistPanel from "./components/Phase5BetaChecklistPanel.jsx";
import PublicDemoWarningBanner from "./components/PublicDemoWarningBanner.jsx";
import PublicDemoHero from "./components/PublicDemoHero.jsx";
import PublicDemoInternalPanel from "./components/PublicDemoInternalPanel.jsx";
import PublicRecommendationIntro from "./components/PublicRecommendationIntro.jsx";

const FAVORITES_STORAGE_KEY = "railyatra_favorite_routes";
const RECENT_SEARCHES_STORAGE_KEY = "railyatra_recent_searches";

function App() {
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [trainType, setTrainType] = useState("All");
  const [journeyClass, setJourneyClass] = useState("SL");
  const [quota, setQuota] = useState("GN");
  const [journeyDate, setJourneyDate] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sourceSuggestions, setSourceSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [sortMode, setSortMode] = useState("best");
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [hideUnknownFare, setHideUnknownFare] = useState(false);
  const [minScore, setMinScore] = useState("");
  const [maxTransferWait, setMaxTransferWait] = useState("");
  const [departureWindow, setDepartureWindow] = useState("all");
  const [maxFare, setMaxFare] = useState("");
  const [expandedCard, setExpandedCard] = useState(null);
  const [compareRoutes, setCompareRoutes] = useState([]);
  const [shareMessage, setShareMessage] = useState("");
  const [apiStatus, setApiStatus] = useState({
    state: "checking",
    label: "Checking backend",
    detail: "Testing RailYatra API connection...",
  });
  const [searchErrorDetails, setSearchErrorDetails] = useState(null);
  const [searchValidation, setSearchValidation] = useState(null);
  const [recentSearches, setRecentSearches] = useState(() => {
    try {
      if (typeof window === "undefined") return [];
      return JSON.parse(localStorage.getItem(RECENT_SEARCHES_STORAGE_KEY) || "[]");
    } catch {
      return [];
    }
  });
  const [favoriteRoutes, setFavoriteRoutes] = useState(() => {
    try {
      if (typeof window === "undefined") return [];
      return JSON.parse(localStorage.getItem(FAVORITES_STORAGE_KEY) || "[]");
    } catch {
      return [];
    }
  });
  const [showFareAdmin, setShowFareAdmin] = useState(false);
  const [fareStats, setFareStats] = useState(null);
  const [fareFiles, setFareFiles] = useState([]);
  const [fareRows, setFareRows] = useState([]);
  const [fareAdminLoading, setFareAdminLoading] = useState(false);
  const [fareAdminMessage, setFareAdminMessage] = useState("");
  const [manualFare, setManualFare] = useState({
    train_no: "",
    source: "",
    destination: "",
    class_code: "SL",
    fare: "",
  });
  const [fareTest, setFareTest] = useState({
    train_no: "",
    source: "",
    destination: "",
    class_code: "SL",
  });
  const [fareTestResult, setFareTestResult] = useState(null);

  const allRecommendations = result?.recommendations || [];

  useEffect(() => {
    let cancelled = false;

    async function checkBackendHealth() {
      try {
        const nextStatus = await fetchBackendHealthStatus();

        if (!cancelled) {
          setApiStatus(nextStatus);
        }
      } catch {
        if (!cancelled) {
          setApiStatus({
            state: "offline",
            label: "Backend offline",
            detail: "Start backend with uvicorn backend.api.main:app --reload",
            meta: "Then click Recheck.",
          });
        }
      }
    }

    checkBackendHealth();
    const timer = setInterval(checkBackendHealth, 30000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const recommendations = useMemo(() => {
    let filtered = allRecommendations;

    if (activeFilter === "smart") {
      filtered = allRecommendations.filter((item) => item.type === "multi_transfer");
    }

    if (activeFilter === "direct") {
      filtered = allRecommendations.filter((item) => item.type === "direct");
    }

    if (activeFilter === "transfer") {
      filtered = allRecommendations.filter((item) => item.type === "one_transfer");
    }

    if (activeFilter === "verified_fare") {
      filtered = allRecommendations.filter((item) => hasVerifiedFare(item));
    }

    if (activeFilter === "low_risk") {
      filtered = allRecommendations.filter(
        (item) => getRouteRisk(item).level === "low"
      );
    }

    if (maxFare) {
      const fareLimit = Number(maxFare);

      if (!Number.isNaN(fareLimit) && fareLimit > 0) {
        filtered = filtered.filter(
          (item) => getRecommendationFare(item) <= fareLimit
        );
      }
    }

    if (departureWindow !== "all") {
      filtered = filtered.filter((item) =>
        matchesDepartureWindow(item, departureWindow)
      );
    }

    if (maxTransferWait) {
      const waitLimit = Number(maxTransferWait);

      if (!Number.isNaN(waitLimit) && waitLimit >= 0) {
        filtered = filtered.filter((item) => {
          const wait = getTransferWaitHours(item);
          return wait === null || wait <= waitLimit;
        });
      }
    }

    const maxTransferWaitFilterNote = "max transfer wait filter active";

    if (minScore) {
      const scoreLimit = Number(minScore);

      if (!Number.isNaN(scoreLimit) && scoreLimit > 0) {
        filtered = filtered.filter((item) => Number(item.score || 0) >= scoreLimit);
      }
    }

    const minimumScoreFilterNote = "minimum score filter active";

    if (hideUnknownFare) {
      filtered = filtered.filter((item) => hasVerifiedFare(item));
    }

    const hideUnknownFareFilterNote = "hide unknown fare filter active";

    const sorted = [...filtered];

    if (sortMode === "best") {
      sorted.sort((a, b) => b.score - a.score);
    }

    if (sortMode === "fastest") {
      sorted.sort(
        (a, b) =>
          getRecommendationDuration(a) - getRecommendationDuration(b)
      );
    }

    if (sortMode === "least_transfers") {
      sorted.sort(
        (a, b) =>
          getRecommendationTransfers(a) - getRecommendationTransfers(b)
      );
    }

    if (sortMode === "cheapest") {
      sorted.sort(
        (a, b) =>
          getRecommendationFare(a) - getRecommendationFare(b) ||
          b.score - a.score
      );
    }

    return sorted;
  }, [allRecommendations, activeFilter, sortMode, maxFare, departureWindow, maxTransferWait, minScore, hideUnknownFare]);

  const bestDirect = useMemo(
    () => allRecommendations.find((item) => item.type === "direct"),
    [allRecommendations]
  );

  const bestTransfer = useMemo(
    () => allRecommendations.find((item) => item.type === "one_transfer"),
    [allRecommendations]
  );

  const bestSmart = useMemo(
    () => allRecommendations.find((item) => item.type === "multi_transfer"),
    [allRecommendations]
  );

  const fastestOption = useMemo(() => {
    if (!allRecommendations.length) return null;

    return [...allRecommendations].sort(
      (a, b) => getRecommendationDuration(a) - getRecommendationDuration(b)
    )[0];
  }, [allRecommendations]);

  const leastTransferOption = useMemo(() => {
    if (!allRecommendations.length) return null;

    return [...allRecommendations].sort(
      (a, b) =>
        getRecommendationTransfers(a) - getRecommendationTransfers(b) ||
        b.score - a.score
    )[0];
  }, [allRecommendations]);

  const fareVerificationSummary = useMemo(() => {
    const total = allRecommendations.length;

    if (!total) {
      return {
        total: 0,
        verified: 0,
        partial: 0,
        estimated: 0,
        coveragePercent: 0,
      };
    }

    const verified = allRecommendations.filter((item) => {
      const coverage = item.fare_coverage;
      return coverage?.status === "full";
    }).length;

    const partial = allRecommendations.filter((item) => {
      const coverage = item.fare_coverage;
      return coverage?.status === "partial";
    }).length;

    const estimated = total - verified - partial;

    const coveragePercent = Math.round(
      ((verified + partial * 0.5) / total) * 100
    );

    return {
      total,
      verified,
      partial,
      estimated,
      coveragePercent,
    };
  }, [allRecommendations]);

  function parseTimeHour(value) {
    if (!value || value === "None" || value === "N/A") return null;

    const text = String(value).trim();
    const match = text.match(/(\d{1,2}):(\d{2})/);

    if (!match) return null;

    const hour = Number(match[1]);

    if (Number.isNaN(hour)) return null;

    return hour;
  }

  function getRecommendationDepartureHour(item) {
    const data = item.data || {};

    if (item.type === "direct") {
      return parseTimeHour(data.departure || data.source_departure);
    }

    if (item.type === "one_transfer") {
      return parseTimeHour(data.source_departure || data.first_departure);
    }

    if (item.type === "multi_transfer") {
      const firstLeg = data.train_legs?.[0];
      return parseTimeHour(firstLeg?.start_time || data.departure);
    }

    return parseTimeHour(data.departure || data.source_departure || data.start_time);
  }

  function matchesDepartureWindow(item, windowName) {
    if (!windowName || windowName === "all") return true;

    const hour = getRecommendationDepartureHour(item);

    if (hour === null) return true;

    if (windowName === "morning") return hour >= 5 && hour < 12;
    if (windowName === "afternoon") return hour >= 12 && hour < 17;
    if (windowName === "evening") return hour >= 17 && hour < 21;
    if (windowName === "night") return hour >= 21 || hour < 5;

    return true;
  }

  function cleanStation(value) {
    return value.trim().toUpperCase();
  }

  function getAdvancedFilterCount() {
    let count = 0;

    if (typeof trainType !== "undefined" && trainType !== "All") count += 1;
    if (typeof quota !== "undefined" && quota !== "GN") count += 1;
    if (typeof maxFare !== "undefined" && maxFare) count += 1;
    if (typeof departureWindow !== "undefined" && departureWindow !== "all") count += 1;
    if (typeof maxTransferWait !== "undefined" && maxTransferWait) count += 1;
    if (typeof minScore !== "undefined" && minScore) count += 1;
    if (typeof hideUnknownFare !== "undefined" && hideUnknownFare) count += 1;

    return count;
  }

  function resetSearchFilters() {
    setJourneyClass("SL");
    setTrainType("All");
    setJourneyDate("");
    setQuota("GN");
    setMaxFare("");
    setActiveFilter("all");
    setSortMode("best");
    setShowAdvancedFilters(false);
    setHideUnknownFare(false);
    setMinScore("");
    setMaxTransferWait("");
    setDepartureWindow("all");
    setExpandedCard(null);
  }

  function swapStations() {
    setSource(destination);
    setDestination(source);
  }


  async function fetchStationSuggestions(value, setter) {
    const query = String(value || "").trim().toUpperCase();

    if (query.length < 2) {
      setter([]);
      return;
    }

    try {
      const params = new URLSearchParams({
        q: query,
        limit: "8",
      });

      const res = await fetch(`${API_BASE}/staging/stations?${params.toString()}`);

      if (!res.ok) {
        setter([]);
        return;
      }

      const data = await res.json();
      setter(Array.isArray(data.stations) ? data.stations : []);
    } catch {
      setter([]);
    }
  }

  function handleMainStationInputChange(event, target) {
    const normalizedValue = String(event?.target?.value || "").toUpperCase();

    if (target === "source") {
      setSource(normalizedValue);
      fetchStationSuggestions(normalizedValue, setSourceSuggestions);
    } else {
      setDestination(normalizedValue);
      fetchStationSuggestions(normalizedValue, setDestinationSuggestions);
    }

    setError("");
  }

  function handleMainStationInputFocus(target) {
    if (target === "source") {
      fetchStationSuggestions(source, setSourceSuggestions);
    } else {
      fetchStationSuggestions(destination, setDestinationSuggestions);
    }
  }

  function handleMainStationInputKeyUp(event, target) {
    const key = event?.key || "";
    const currentValue = String(event?.currentTarget?.value || "");

    if (["Backspace", "Delete", "ArrowDown", "ArrowUp"].includes(key)) {
      if (target === "source") {
        fetchStationSuggestions(currentValue, setSourceSuggestions);
      } else {
        fetchStationSuggestions(currentValue, setDestinationSuggestions);
      }
    }
  }







  function getStationCode(station) {
    return station.station_code || station.code || station.id || "";
  }

  function getStationName(station) {
    const validationIssue = validateSearchFormValues();

    if (validationIssue) {
      setSearchValidation(validationIssue);

      if (typeof setSearchErrorDetails === "function") {
        setSearchErrorDetails(null);
      }

      if (typeof setError === "function") {
        setError("");
      }

      if (typeof setLoading === "function") {
        setLoading(false);
      }

      if (typeof setIsLoading === "function") {
        setIsLoading(false);
      }

      return;
    }

    setSearchValidation(null);

    return station.station_name || station.name || station.city || "";
  }

  async function searchJourney(e) {
    e.preventDefault();

    const from = cleanStation(source);
    const to = cleanStation(destination);

    if (!from || !to) {
      setError("Please enter both station codes.");
      return;
    }

    if (from === to) {
      setError("Source and destination cannot be same.");
      return;
    }

    setSource(from);
    setDestination(to);
    setLoading(true);
    setSearchErrorDetails(null);
    setError("");
    setResult(null);
    setActiveFilter("all");
    setSortMode("best");
    setExpandedCard(null);

    try {
      const res = await fetch(
      API_BASE +
        "/search?source=" +
        from +
        "&destination=" +
        to +
        "&limit=10" +
        "&class_code=" +
        journeyClass +
        "&train_type=" +
        encodeURIComponent(trainType) +
        "&quota=" +
        encodeURIComponent(quota) +
        (journeyDate ? "&journey_date=" + encodeURIComponent(journeyDate) : "")
      );

      if (!res.ok) throw new Error("Search failed");

      const data = await res.json();
      setResult(data);
      addRecentSearch(from, to);
    } catch {
      setError("Backend not connected. Start FastAPI on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  function setQuickRoute(from, to) {
    setSource(from);
    setDestination(to);
  }

  async function loadFareAdminData() {
    setFareAdminLoading(true);
    setFareAdminMessage("");

    try {
      const statsResponse = await fetch("http://127.0.0.1:8000/fares/stats");
      const statsData = await statsResponse.json();

      const filesResponse = await fetch("http://127.0.0.1:8000/fares/import/files");
      const filesData = await filesResponse.json();

      const faresResponse = await fetch("http://127.0.0.1:8000/fares?limit=20");
      const faresData = await faresResponse.json();

      setFareStats(statsData);
      setFareFiles(filesData.files || []);
      setFareRows(faresData.fares || []);
    } catch (err) {
      setFareAdminMessage("Could not load fare admin data. Check backend server.");
    } finally {
      setFareAdminLoading(false);
    }
  }

  function toggleFareAdmin() {
    setShowFareAdmin((current) => !current);
  }

  async function importFareFile(fileName) {
    setFareAdminLoading(true);
    setFareAdminMessage("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/fares/import?csv_file=${encodeURIComponent(fileName)}`,
        { method: "POST" }
      );

      if (!response.ok) {
        let errorMessage = `Search API returned HTTP ${response.status}`;

        try {
          const errorPayload = await response.clone().json();
          errorMessage = errorPayload.detail || errorPayload.message || errorMessage;
        } catch {}

        const apiError = new Error(errorMessage);
        apiError.statusCode = response.status;
        setSearchErrorDetails(buildSearchErrorDetails(apiError, response.status));
        throw apiError;
      }

      const data = await response.json();

      if (!data.success) {
        setFareAdminMessage(data.message || "Import failed");
      } else {
        const imported = data.result?.imported ?? 0;
        const skipped = data.result?.skipped ?? 0;
        setFareAdminMessage(`Import completed: ${imported} imported, ${skipped} skipped`);
      }

      await loadFareAdminData();
    } catch (err) {
      setFareAdminMessage("Import failed. Check backend server.");
    } finally {
      setFareAdminLoading(false);
    }
  }

  function updateManualFareField(field, value) {
    setManualFare((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function submitManualFare(event) {
    event.preventDefault();

    if (
      !manualFare.train_no ||
      !manualFare.source ||
      !manualFare.destination ||
      !manualFare.fare
    ) {
      setFareAdminMessage("Please fill train no, source, destination and fare.");
      return;
    }

    setFareAdminLoading(true);
    setFareAdminMessage("");

    try {
      const params = new URLSearchParams({
        train_no: manualFare.train_no,
        source: manualFare.source,
        destination: manualFare.destination,
        class_code: manualFare.class_code || "SL",
        fare: manualFare.fare,
      });

      const response = await fetch(
        `http://127.0.0.1:8000/fare/manual?${params.toString()}`,
        { method: "POST" }
      );

      const data = await response.json();

      if (!data.success) {
        setFareAdminMessage(data.message || "Manual fare save failed");
      } else {
        setFareAdminMessage("Manual verified fare saved successfully.");

        setManualFare({
          train_no: "",
          source: "",
          destination: "",
          class_code: "SL",
          fare: "",
        });

        await loadFareAdminData();
      }
    } catch (err) {
      setFareAdminMessage("Manual fare save failed. Check backend server.");
    } finally {
      setFareAdminLoading(false);
    }
  }

  function updateFareTestField(field, value) {
    setFareTest((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function checkFareCoverage(event) {
    event.preventDefault();

    if (!fareTest.train_no || !fareTest.source || !fareTest.destination) {
      setFareAdminMessage("Please fill train no, source and destination for fare check.");
      return;
    }

    setFareAdminLoading(true);
    setFareAdminMessage("");
    setFareTestResult(null);

    try {
      const params = new URLSearchParams({
        train_no: fareTest.train_no,
        source: fareTest.source,
        destination: fareTest.destination,
        class_code: fareTest.class_code || "SL",
      });

      const response = await fetch(
        `http://127.0.0.1:8000/fare/lookup?${params.toString()}`
      );

      const data = await response.json();
      setFareTestResult(data);
    } catch (err) {
      setFareAdminMessage("Fare check failed. Check backend server.");
    } finally {
      setFareAdminLoading(false);
    }
  }

  function saveRecentSearches(nextSearches) {
    setRecentSearches(nextSearches);

    try {
      localStorage.setItem(RECENT_SEARCHES_STORAGE_KEY, JSON.stringify(nextSearches));
    } catch {
      setShareMessage("Could not save recent search.");
      setTimeout(() => setShareMessage(""), 2200);
    }
  }

  function addRecentSearch(from, to) {
    const search = {
      key: [
        from,
        to,
        journeyClass,
        trainType,
        typeof journeyDate !== "undefined" ? journeyDate : "",
        typeof quota !== "undefined" ? quota : "",
        typeof maxFare !== "undefined" ? maxFare : "",
      ].join("|"),
      source: from,
      destination: to,
      journeyClass,
      trainType,
      journeyDate: typeof journeyDate !== "undefined" ? journeyDate : "",
      quota: typeof quota !== "undefined" ? quota : "GN",
      maxFare: typeof maxFare !== "undefined" ? maxFare : "",
      savedAt: new Date().toISOString(),
    };

    const withoutDuplicate = recentSearches.filter((item) => item.key !== search.key);
    const nextSearches = [search, ...withoutDuplicate].slice(0, 8);

    saveRecentSearches(nextSearches);
  }

  function loadRecentSearch(search) {
    setSource(search.source);
    setDestination(search.destination);
    setJourneyClass(search.journeyClass || "SL");
    setTrainType(search.trainType || "All");

    if (typeof setJourneyDate !== "undefined") {
      setJourneyDate(search.journeyDate || "");
    }

    if (typeof setQuota !== "undefined") {
      setQuota(search.quota || "GN");
    }

    if (typeof setMaxFare !== "undefined") {
      setMaxFare(search.maxFare || "");
    }

    setActiveFilter("all");
    setSortMode("best");
    setExpandedCard(null);
  }

  function clearRecentSearches() {
    saveRecentSearches([]);
    setShareMessage("Recent searches cleared.");
    setTimeout(() => setShareMessage(""), 2200);
  }

  function renderRecentSearchesPanel() {
    if (!recentSearches.length) return null;

    return (
      <div className="recent-searches-panel">
        <div className="recent-searches-header">
          <div>
            <span>Recent searches</span>
            <strong>
              {recentSearches.length} saved search
              {recentSearches.length > 1 ? "es" : ""}
            </strong>
          </div>

          <button type="button" onClick={clearRecentSearches}>
            Clear
          </button>
        </div>

        <div className="recent-searches-list">
          {recentSearches.map((search) => (
            <button
              type="button"
              className="recent-search-row"
              key={search.key}
              onClick={() => loadRecentSearch(search)}
            >
              <strong>{search.source} → {search.destination}</strong>
              <span>
                {(search.journeyClass || "SL") + " · " +
                  (search.trainType || "All") + " · " +
                  (search.journeyDate || "No date") + " · " +
                  (search.quota || "GN") + " · " +
                  (search.maxFare ? `Max ₹${search.maxFare}` : "No fare limit")}
              </span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  function renderFareAdminPanel() {
    return (
      <div className="fare-admin-wrapper">
        <button
          type="button"
          className="fare-admin-toggle"
          onClick={toggleFareAdmin}
        >
          {showFareAdmin ? "Hide fare admin" : "Open fare admin"}
        </button>

        {showFareAdmin && (
          <div className="fare-admin-panel">
            <div className="fare-admin-header">
              <div>
                <span>Fare Admin</span>
                <h3>Real fare table manager</h3>
              </div>

              <button
                type="button"
                onClick={loadFareAdminData}
                disabled={fareAdminLoading}
              >
                Refresh
              </button>
            </div>

            {fareAdminLoading && (
              <div className="fare-admin-message">Loading fare data...</div>
            )}

            {fareAdminMessage && (
              <div className="fare-admin-message">{fareAdminMessage}</div>
            )}

            {fareStats && (
              <div className="fare-admin-stats">
                <div>
                  <span>Total fares</span>
                  <strong>{fareStats.total_rows}</strong>
                </div>

                <div>
                  <span>Trains</span>
                  <strong>{fareStats.train_count}</strong>
                </div>

                <div>
                  <span>Classes</span>
                  <strong>{fareStats.class_count}</strong>
                </div>
              </div>
            )}

            <div className="fare-admin-section">
              <h4>Add manual verified fare</h4>

              <form className="manual-fare-form" onSubmit={submitManualFare}>
                <div className="manual-fare-grid">
                  <label>
                    <span>Train no</span>
                    <input
                      value={manualFare.train_no}
                      onChange={(e) =>
                        updateManualFareField("train_no", e.target.value.toUpperCase())
                      }
                      placeholder="12303"
                    />
                  </label>

                  <label>
                    <span>Source</span>
                    <input
                      value={manualFare.source}
                      onChange={(e) =>
                        updateManualFareField("source", e.target.value.toUpperCase())
                      }
                      placeholder="PNBE"
                    />
                  </label>

                  <label>
                    <span>Destination</span>
                    <input
                      value={manualFare.destination}
                      onChange={(e) =>
                        updateManualFareField("destination", e.target.value.toUpperCase())
                      }
                      placeholder="NDLS"
                    />
                  </label>

                  <label>
                    <span>Class</span>
                    <input
                      value={manualFare.class_code}
                      onChange={(e) =>
                        updateManualFareField("class_code", e.target.value.toUpperCase())
                      }
                      placeholder="SL"
                    />
                  </label>

                  <label>
                    <span>Fare</span>
                    <input
                      type="number"
                      min="1"
                      value={manualFare.fare}
                      onChange={(e) =>
                        updateManualFareField("fare", e.target.value)
                      }
                      placeholder="590"
                    />
                  </label>
                </div>

                <button type="submit" disabled={fareAdminLoading}>
                  Save manual fare
                </button>
              </form>

              {fareFiles.map((file) => (
                <div className="fare-file-row" key={file.file}>
                  <div>
                    <strong>{file.file}</strong>
                    <span>{file.path}</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => importFareFile(file.file)}
                    disabled={fareAdminLoading}
                  >
                    Import
                  </button>
                </div>
              ))}
            </div>

            <div className="fare-admin-section">
              <h4>Quick fare coverage test</h4>

              <form className="fare-test-form" onSubmit={checkFareCoverage}>
                <div className="manual-fare-grid">
                  <label>
                    <span>Train no</span>
                    <input
                      value={fareTest.train_no}
                      onChange={(e) =>
                        updateFareTestField("train_no", e.target.value.toUpperCase())
                      }
                      placeholder="12309"
                    />
                  </label>

                  <label>
                    <span>Source</span>
                    <input
                      value={fareTest.source}
                      onChange={(e) =>
                        updateFareTestField("source", e.target.value.toUpperCase())
                      }
                      placeholder="PNBE"
                    />
                  </label>

                  <label>
                    <span>Destination</span>
                    <input
                      value={fareTest.destination}
                      onChange={(e) =>
                        updateFareTestField("destination", e.target.value.toUpperCase())
                      }
                      placeholder="NDLS"
                    />
                  </label>

                  <label>
                    <span>Class</span>
                    <input
                      value={fareTest.class_code}
                      onChange={(e) =>
                        updateFareTestField("class_code", e.target.value.toUpperCase())
                      }
                      placeholder="SL"
                    />
                  </label>
                </div>

                <button type="submit" disabled={fareAdminLoading}>
                  Check fare
                </button>
              </form>

              {fareTestResult && (
                <div
                  className={
                    fareTestResult.found
                      ? "fare-test-result found"
                      : "fare-test-result not-found"
                  }
                >
                  <strong>
                    {fareTestResult.found
                      ? `Verified fare found ₹${fareTestResult.fare}`
                      : "Fare not found"}
                  </strong>

                  <span>
                    {fareTestResult.found
                      ? `${fareTestResult.train_no} · ${fareTestResult.source} → ${fareTestResult.destination} · ${fareTestResult.class_code} · ${fareTestResult.provider}`
                      : fareTestResult.message}
                  </span>
                </div>
              )}
            </div>

            <div className="fare-admin-section">
              <h4>Recent fare rows</h4>

              {fareRows.length === 0 && (
                <p>No real fare rows loaded yet.</p>
              )}

              {fareRows.length > 0 && (
                <div className="fare-table">
                  <div className="fare-table-head">
                    <span>Train</span>
                    <span>Route</span>
                    <span>Class</span>
                    <span>Fare</span>
                  </div>

                  {fareRows.map((row) => (
                    <div className="fare-table-row" key={row.id}>
                      <span>{row.train_no}</span>
                      <span>{row.source} → {row.destination}</span>
                      <span>{row.class_code}</span>
                      <strong>₹{row.fare}</strong>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  function safeValue(value) {
    if (value === null || value === undefined || value === "None") {
      return "N/A";
    }
    return value;
  }

  function getRecommendationFare(item) {
    const fare = item.fare || {};
    const data = item.data || {};

    const values = [
      fare.estimated_after_split,
      fare.estimated_fare,
      fare.total_fare,
      fare.fare,
      fare.amount,
      data.estimated_fare,
      data.fare,
    ];

    for (const value of values) {
      const numeric = Number(value);
      if (!Number.isNaN(numeric) && numeric > 0) return numeric;
    }

    return 999999;
  }

  function getTransferWaitHours(item) {
    const data = item.data || {};

    if (item.type === "direct") return 0;

    const values = [
      data.transfer_wait_hours,
      data.max_transfer_wait_hours,
      data.total_wait_hours,
      data.wait_hours,
    ];

    for (const value of values) {
      const numeric = Number(value);

      if (!Number.isNaN(numeric) && numeric >= 0) {
        return numeric;
      }
    }

    return null;
  }

  function getRecommendationDuration(item) {
    const data = item.data || {};

    if (item.type === "multi_transfer") {
      return data.total_duration_hours || 9999;
    }

    if (item.type === "direct") {
      return data.duration_hours || 9999;
    }

    if (item.type === "one_transfer") {
      return data.total_duration_hours || 9999;
    }

    return 9999;
  }

  function getRecommendationTransfers(item) {
    const data = item.data || {};

    if (item.type === "multi_transfer") {
      return data.transfers || 0;
    }

    if (item.type === "direct") {
      return 0;
    }

    if (item.type === "one_transfer") {
      return 1;
    }

    return 99;
  }

  function toggleDetails(cardId) {
    setExpandedCard(expandedCard === cardId ? null : cardId);
  }

  function getRecommendationTitle(item) {
    if (!item) return "Not available";

    const data = item.data || {};

    if (item.type === "multi_transfer") {
      return data.summary || item.label;
    }

    if (item.type === "direct") {
      return `${data.train_no} ${data.train_name}`;
    }

    if (item.type === "one_transfer") {
      return `${data.first_train} + ${data.second_train}`;
    }

    return item.label || "Journey option";
  }

  function getRecommendationSubtext(item) {
    if (!item) return "";

    const duration = getRecommendationDuration(item);
    const transfers = getRecommendationTransfers(item);

    const durationText = duration === 9999 ? "Duration N/A" : `${duration} hrs`;
    const transferText = transfers === 0 ? "No transfer" : `${transfers} transfer`;

    return `${durationText} · ${transferText} · Score ${item.score}`;
  }

  function getRouteTags(item) {
    const data = item.data || {};
    const tags = [];

    const title = getRecommendationTitle(item).toUpperCase();
    const duration = getRecommendationDuration(item);
    const transfers = getRecommendationTransfers(item);

    if (title.includes("RAJDHANI")) tags.push("Premium");
    if (title.includes("DURONTO")) tags.push("Fast");
    if (title.includes("SHATABDI")) tags.push("Premium");
    if (title.includes("VANDE")) tags.push("Premium");

    if (duration !== 9999 && duration <= 13) tags.push("Fast");
    if (duration !== 9999 && duration > 13 && duration <= 18) tags.push("Overnight");

    if (transfers === 0) tags.push("No transfer");
    if (transfers === 1) tags.push("One transfer");

    if (item.type === "one_transfer") {
      if ((data.transfer_wait_hours || 999) <= 1.5) tags.push("Low wait");

      const hub = data.transfer_station;
      if (["MGS", "DDU", "BSB", "PRYJ", "CNB", "GZB", "LKO"].includes(hub)) {
        tags.push("Transfer hub");
      }
    }

    if (item.type === "multi_transfer") {
      const firstLeg = data.train_legs?.[0];

      if (firstLeg?.quality_bonus >= 200) tags.push("High quality train");
    }

    return [...new Set(tags)].slice(0, 4);
  }

  function renderRouteTags(item) {
    const tags = getRouteTags(item);

    if (!tags.length) return null;

    return (
      <div className="quality-tags">
        {tags.map((tag, index) => (
          <span key={index}>{tag}</span>
        ))}
      </div>
    );
  }

  function getRouteRisk(item) {
    const data = item.data || {};
    const transfers = getRecommendationTransfers(item);

    if (transfers === 0) {
      return {
        level: "low",
        label: "Low risk",
        reason: "No train change required",
      };
    }

    if (item.type === "one_transfer") {
      const wait = data.transfer_wait_hours || 0;
      const hub = data.transfer_station;
      const strongHubs = ["MGS", "DDU", "BSB", "PRYJ", "CNB", "GZB", "LKO", "NDLS"];

      if (wait < 0.5) {
        return {
          level: "high",
          label: "High risk",
          reason: "Transfer wait is too short",
        };
      }

      if (!strongHubs.includes(hub)) {
        return {
          level: "medium",
          label: "Medium risk",
          reason: "Transfer station is not a preferred hub",
        };
      }

      if (wait >= 0.75 && wait <= 3) {
        return {
          level: "low",
          label: "Low risk",
          reason: "Healthy wait time at major transfer hub",
        };
      }

      if (wait > 5) {
        return {
          level: "medium",
          label: "Medium risk",
          reason: "Long transfer wait",
        };
      }

      return {
        level: "medium",
        label: "Medium risk",
        reason: "Transfer timing needs attention",
      };
    }

    if (item.type === "multi_transfer") {
      if (transfers === 1) {
        return {
          level: "medium",
          label: "Medium risk",
          reason: "One smart train change required",
        };
      }

      return {
        level: "high",
        label: "High risk",
        reason: "Multiple train changes required",
      };
    }

    return {
      level: "medium",
      label: "Medium risk",
      reason: "Journey risk not fully known",
    };
  }

  function renderRiskBadge(item) {
    const risk = getRouteRisk(item);

    return (
      <div className={`risk-badge risk-${risk.level}`}>
        <strong>{risk.label}</strong>
        <span>{risk.reason}</span>
      </div>
    );
  }

  function renderFareBox(item) {
    const fare = item.fare;

    if (!fare) return null;

    return (
      <div className="fare-box">
        <div>
          <span>Estimated fare</span>
          <strong>₹{fare.estimated_fare}</strong>
        </div>

        <div>
          <span>Possible saving</span>
          <strong>₹{fare.split_saving_estimate}</strong>
        </div>

        <p>
          After split estimate: ₹{fare.estimated_after_split} · Confidence:{" "}
          {fare.confidence} · Source:{" "}
          {fare.fare_source === "fare_table" ? "Fare table" : "Estimate"} · Class:{" "}
          {fare.class_code || "SL"}
        </p>
      </div>
    );
  }

  function renderSplitTicketBox(item) {
    const split = item.split_ticket;

    if (!split || !split.recommended) return null;

    return (
      <div className="split-ticket-box">
        <div className="split-ticket-header">
          <span>Split-ticket intelligence</span>
          <strong>Save ₹{split.estimated_saving}</strong>
        </div>

        <p>{split.reason}</p>

        <div className="split-ticket-meta">
          <span>Original ₹{split.estimated_original_fare}</span>
          <span>After split ₹{split.estimated_split_fare}</span>
          <span>{split.ticket_count} tickets</span>
          <span>{split.confidence} confidence</span>
        </div>

        {split.segments?.length > 0 && (
          <ul className="split-segments">
            {split.segments.map((segment, index) => (
              <li key={index}>
                <strong>{segment.from} → {segment.to}</strong>
                <span>
                  {segment.train_no} · ₹{segment.estimated_fare}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  function getFareSourceInfo(item) {
    if (!item || !item.fare) {
      return {
        label: "Fare unavailable",
        className: "unknown",
      };
    }

    if (item.fare.fare_source === "fare_table") {
      return {
        label: "Verified fare",
        className: "verified",
      };
    }

    return {
      label: "Estimated fare",
      className: "estimate",
    };
  }

  function renderComparisonFareIndicator(item) {
    const info = getFareSourceInfo(item);

    return (
      <div className={`comparison-fare-source ${info.className}`}>
        {info.label}
      </div>
    );
  }

  function renderFareCoverageMeter(item) {
    const coverage = item.fare_coverage;

    if (!coverage || coverage.total_segments === 0) return null;

    return (
      <div className={`fare-coverage-box coverage-${coverage.status}`}>
        <div className="fare-coverage-head">
          <span>{coverage.label}</span>
          <strong>{coverage.coverage_percent}%</strong>
        </div>

        <div className="fare-coverage-track">
          <div
            className="fare-coverage-fill"
            style={{ width: `${coverage.coverage_percent}%` }}
          />
        </div>

        <p>
          {coverage.verified_segments}/{coverage.total_segments} fare segments verified
        </p>
      </div>
    );
  }

  function hasVerifiedFare(item) {
    const coverage = item.fare_coverage;
    const fare = item.fare;

    if (coverage && (coverage.verified_segments || 0) > 0) {
      return true;
    }

    if (fare && fare.fare_source === "fare_table") {
      return true;
    }

    return false;
  }

  function renderFareVerificationSummary() {
    if (!fareVerificationSummary.total) return null;

    return (
      <div className="fare-summary-box">
        <div>
          <span>Fare verification</span>
          <strong>
            {fareVerificationSummary.verified} verified journeys out of{" "}
            {fareVerificationSummary.total}
          </strong>
        </div>

        <div className="fare-summary-meter">
          <div
            className="fare-summary-fill"
            style={{ width: `${fareVerificationSummary.coveragePercent}%` }}
          />
        </div>

        <p>
          {fareVerificationSummary.coveragePercent}% fare coverage ·{" "}
          {fareVerificationSummary.partial} partial ·{" "}
          {fareVerificationSummary.estimated} estimated
        </p>
      </div>
    );
  }

  function buildJourneyShareText(item) {
    const data = item.data || {};
    const fare = item.fare || {};
    const split = item.split_ticket || {};
    const coverage = item.fare_coverage || {};

    const title = getRecommendationTitle(item);
    const duration = getRecommendationDuration(item);
    const transfers = getRecommendationTransfers(item);

    const lines = [];

    lines.push("RailYatra Journey Option");
    lines.push("------------------------");
    lines.push(`Route: ${source} → ${destination}`);
    lines.push(`Class: ${journeyClass}`);
    if (maxFare) lines.push(`Max fare: ₹${maxFare}`);
    lines.push(`Quota: ${quota}`);
    lines.push(`Journey date: ${journeyDate || "Not selected"}`);
    lines.push(`Train type: ${trainType}`);
    lines.push(`Option: ${title}`);
    lines.push(`Type: ${item.label || item.type}`);
    lines.push(
      `Duration: ${duration === 9999 ? "N/A" : `${duration} hrs`}`
    );
    lines.push(
      `Transfers: ${transfers === 0 ? "No transfer" : transfers}`
    );

    if (fare.estimated_fare) {
      lines.push(`Fare: ₹${fare.estimated_fare}`);
      lines.push(
        `Fare source: ${
          fare.fare_source === "fare_table" ? "Verified fare table" : "Estimate"
        }`
      );
    }

    if (coverage.label) {
      lines.push(`Fare coverage: ${coverage.label}`);
    }

    if (split.recommended) {
      lines.push(`Split-ticket saving: ₹${split.estimated_saving}`);
      lines.push(`Split strategy: ${split.strategy}`);
    }

    if (item.type === "direct") {
      lines.push(`Train: ${data.train_no} - ${data.train_name}`);
      lines.push(`Departure: ${safeValue(data.departure)}`);
      lines.push(`Arrival: ${safeValue(data.arrival)}`);
    }

    if (item.type === "one_transfer") {
      lines.push(`First train: ${data.first_train} - ${data.first_train_name}`);
      lines.push(`Transfer at: ${data.transfer_station}`);
      lines.push(`Second train: ${data.second_train} - ${data.second_train_name}`);
      lines.push(`Wait time: ${safeValue(data.transfer_wait_hours)} hrs`);
    }

    if (item.type === "multi_transfer" && data.train_legs?.length) {
      lines.push("Train legs:");

      data.train_legs.forEach((leg, index) => {
        lines.push(
          `${index + 1}. ${leg.from} → ${leg.to} by ${leg.train_no} ${leg.train_name || ""}`
        );
      });
    }

    lines.push("------------------------");
    lines.push("Generated by RailYatra");

    return lines.join("\n");
  }

  async function copyJourney(item) {
    const text = buildJourneyShareText(item);

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      setShareMessage("Journey summary copied.");
      setTimeout(() => setShareMessage(""), 2200);
    } catch (err) {
      setShareMessage("Could not copy journey summary.");
      setTimeout(() => setShareMessage(""), 2200);
    }
  }

  function saveFavoriteRoutes(nextFavorites) {
    setFavoriteRoutes(nextFavorites);

    try {
      localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(nextFavorites));
    } catch {
      setShareMessage("Could not save favorite route.");
      setTimeout(() => setShareMessage(""), 2200);
    }
  }

  function getFavoriteRouteKey(item) {
    const data = item.data || {};

    if (item.type === "direct") {
      return `direct-${source}-${destination}-${data.train_no}`;
    }

    if (item.type === "one_transfer") {
      return `transfer-${source}-${destination}-${data.first_train}-${data.transfer_station}-${data.second_train}`;
    }

    if (item.type === "multi_transfer") {
      const preview = data.route_preview?.join("-") || data.summary || "";
      const legs = data.train_legs?.map((leg) => leg.train_no).join("-") || "";
      return `smart-${source}-${destination}-${preview}-${legs}`;
    }

    return `${source}-${destination}-${getRecommendationTitle(item)}`;
  }

  function isFavoriteRoute(item) {
    const key = getFavoriteRouteKey(item);
    return favoriteRoutes.some((route) => route.key === key);
  }

  function toggleFavoriteRoute(item) {
    const key = getFavoriteRouteKey(item);
    const alreadySaved = favoriteRoutes.some((route) => route.key === key);

    if (alreadySaved) {
      const nextFavorites = favoriteRoutes.filter((route) => route.key !== key);
      saveFavoriteRoutes(nextFavorites);
      setShareMessage("Favorite route removed.");
      setTimeout(() => setShareMessage(""), 2200);
      return;
    }

    const favorite = {
      key,
      title: getRecommendationTitle(item),
      subtext: getRecommendationSubtext(item),
      source,
      destination,
      type: item.label || item.type,
      savedAt: new Date().toISOString(),
    };

    const nextFavorites = [favorite, ...favoriteRoutes].slice(0, 20);
    saveFavoriteRoutes(nextFavorites);
    setShareMessage("Route saved to favorites.");
    setTimeout(() => setShareMessage(""), 2200);
  }

  function clearFavoriteRoutes() {
    saveFavoriteRoutes([]);
    setShareMessage("Favorite routes cleared.");
    setTimeout(() => setShareMessage(""), 2200);
  }

  function renderFavoriteButton(item) {
    const saved = isFavoriteRoute(item);

    return (
      <button
        type="button"
        className={saved ? "share-journey-btn favorite-active" : "share-journey-btn"}
        onClick={() => toggleFavoriteRoute(item)}
      >
        {saved ? "★ Saved" : "☆ Save route"}
      </button>
    );
  }

  function renderFavoritesPanel() {
    if (!favoriteRoutes.length) return null;

    return (
      <div className="favorites-panel">
        <div className="favorites-header">
          <div>
            <span>Saved routes</span>
            <strong>{favoriteRoutes.length} favorite route{favoriteRoutes.length > 1 ? "s" : ""}</strong>
          </div>

          <button type="button" onClick={clearFavoriteRoutes}>
            Clear
          </button>
        </div>

        <div className="favorites-list">
          {favoriteRoutes.slice(0, 5).map((route) => (
            <div className="favorite-row" key={route.key}>
              <strong>{route.title}</strong>
              <span>{route.source} → {route.destination} · {route.type}</span>
              <small>{route.subtext}</small>
            </div>
          ))}
        </div>
      </div>
    );
  }

  function getCompareRouteKey(item) {
    const data = item.data || {};

    if (item.type === "direct") {
      return `compare-direct-${source}-${destination}-${data.train_no}`;
    }

    if (item.type === "one_transfer") {
      return `compare-transfer-${source}-${destination}-${data.first_train}-${data.transfer_station}-${data.second_train}`;
    }

    if (item.type === "multi_transfer") {
      const preview = data.route_preview?.join("-") || data.summary || "";
      const legs = data.train_legs?.map((leg) => leg.train_no).join("-") || "";
      return `compare-smart-${source}-${destination}-${preview}-${legs}`;
    }

    return `compare-${source}-${destination}-${getRecommendationTitle(item)}`;
  }

  function isRouteInCompare(item) {
    const key = getCompareRouteKey(item);
    return compareRoutes.some((route) => route.key === key);
  }

  function toggleCompareRoute(item) {
    const key = getCompareRouteKey(item);
    const alreadySelected = compareRoutes.some((route) => route.key === key);

    if (alreadySelected) {
      setCompareRoutes(compareRoutes.filter((route) => route.key !== key));
      return;
    }

    if (compareRoutes.length >= 3) {
      setShareMessage("You can compare maximum 3 routes.");
      setTimeout(() => setShareMessage(""), 2200);
      return;
    }

    const data = item.data || {};
    const fare = item.fare || {};
    const split = item.split_ticket || {};
    const coverage = item.fare_coverage || {};
    const duration = getRecommendationDuration(item);
    const transfers = getRecommendationTransfers(item);

    const compareItem = {
      key,
      title: getRecommendationTitle(item),
      subtext: getRecommendationSubtext(item),
      type: item.label || item.type,
      score: item.score || 0,
      duration,
      transfers,
      fare: fare.estimated_fare || fare.estimated_after_split || "N/A",
      saving: split.recommended ? split.estimated_saving : "N/A",
      coverage: coverage.label || "N/A",
      route: data.route_preview?.join(" → ") || data.summary || `${source} → ${destination}`,
    };

    setCompareRoutes([...compareRoutes, compareItem]);
  }

  function clearCompareRoutes() {
    setCompareRoutes([]);
  }

  function renderCompareButton(item) {
    const selected = isRouteInCompare(item);

    return (
      <button
        type="button"
        className={selected ? "share-journey-btn compare-active" : "share-journey-btn"}
        onClick={() => toggleCompareRoute(item)}
      >
        {selected ? "✓ In Compare" : "Compare"}
      </button>
    );
  }

  function renderComparePanel() {
    if (!compareRoutes.length) return null;

    return (
      <div className="compare-panel">
        <div className="compare-header">
          <div>
            <span>Route comparison</span>
            <strong>{compareRoutes.length}/3 selected</strong>
          </div>

          <button type="button" onClick={clearCompareRoutes}>
            Clear compare
          </button>
        </div>

        <div className="compare-grid">
          {compareRoutes.map((route) => (
            <div className="compare-card" key={route.key}>
              <h4>{route.title}</h4>
              <p>{route.subtext}</p>

              <div className="compare-row">
                <span>Type</span>
                <strong>{route.type}</strong>
              </div>

              <div className="compare-row">
                <span>Score</span>
                <strong>{route.score}</strong>
              </div>

              <div className="compare-row">
                <span>Duration</span>
                <strong>{route.duration === 9999 ? "N/A" : `${route.duration} hrs`}</strong>
              </div>

              <div className="compare-row">
                <span>Transfers</span>
                <strong>{route.transfers === 0 ? "No transfer" : route.transfers}</strong>
              </div>

              <div className="compare-row">
                <span>Fare</span>
                <strong>{route.fare === "N/A" ? "N/A" : `₹${route.fare}`}</strong>
              </div>

              <div className="compare-row">
                <span>Split saving</span>
                <strong>{route.saving === "N/A" ? "N/A" : `₹${route.saving}`}</strong>
              </div>

              <div className="compare-row">
                <span>Coverage</span>
                <strong>{route.coverage}</strong>
              </div>

              <div className="compare-route">{route.route}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  function getShareFareText(item) {
    const fare = item.fare || {};
    const values = [
      fare.estimated_after_split,
      fare.estimated_fare,
      fare.total_fare,
      fare.fare,
      fare.amount,
    ];

    for (const value of values) {
      const numeric = Number(value);

      if (!Number.isNaN(numeric) && numeric > 0) {
        return `₹${numeric}`;
      }
    }

    return "Fare not available";
  }

  function getShareTrainText(item) {
    const data = item.data || {};

    if (item.type === "direct") {
      return data.train_no
        ? `${data.train_no}${data.train_name ? " - " + data.train_name : ""}`
        : "Direct train";
    }

    if (item.type === "one_transfer") {
      return `${data.first_train || "Train 1"} + ${data.second_train || "Train 2"} via ${data.transfer_station || "transfer"}`;
    }

    if (item.type === "multi_transfer") {
      const trains = data.train_legs?.map((leg) => leg.train_no).filter(Boolean);

      if (trains?.length) {
        return trains.join(" + ");
      }

      return "Smart multi-train route";
    }

    return "RailYatra route";
  }

  function buildWhatsAppRouteMessage(item) {
    const data = item.data || {};
    const split = item.split_ticket || {};
    const coverage = item.fare_coverage || {};
    const title = getRecommendationTitle(item);
    const subtext = getRecommendationSubtext(item);
    const duration = getRecommendationDuration(item);
    const transfers = getRecommendationTransfers(item);
    const routeText = data.route_preview?.join(" → ") || data.summary || `${source} → ${destination}`;
    const trainText = getShareTrainText(item);
    const fareText = getShareFareText(item);
    const classText = typeof journeyClass !== "undefined" ? journeyClass : "SL";
    const trainTypeText = typeof trainType !== "undefined" ? trainType : "All";
    const quotaText = typeof quota !== "undefined" ? quota : "GN";
    const dateText = typeof journeyDate !== "undefined" && journeyDate ? journeyDate : "Not selected";
    const scoreText = item.score ? `${item.score}/1000` : "N/A";
    const transferText = transfers === 0 ? "No transfer" : `${transfers} transfer${transfers > 1 ? "s" : ""}`;
    const durationText = duration === 9999 ? "N/A" : `${duration} hrs`;
    const savingText = split.recommended && split.estimated_saving
      ? `₹${split.estimated_saving}`
      : "No split saving";
    const coverageText = coverage.label || "N/A";
    const risk = typeof getRouteRisk === "function" ? getRouteRisk(item) : null;
    const riskText = risk ? `${risk.label || risk.level || "N/A"}` : "N/A";

    return [
      "🚆 RailYatra Smart Route",
      "",
      `Route: ${source} → ${destination}`,
      `Best option: ${title}`,
      `Details: ${subtext}`,
      `Path: ${routeText}`,
      `Train: ${trainText}`,
      "",
      `Class: ${classText}`,
      `Quota: ${quotaText}`,
      `Journey date: ${dateText}`,
      `Train type filter: ${trainTypeText}`,
      "",
      `Duration: ${durationText}`,
      `Transfer: ${transferText}`,
      `Fare: ${fareText}`,
      `Split saving: ${savingText}`,
      `Fare coverage: ${coverageText}`,
      `Risk: ${riskText}`,
      `Score: ${scoreText}`,
      "",
      "Shared from RailYatra"
    ].join("\n");
  }

  async function shareRouteToClipboard(item) {
    const message = buildWhatsAppRouteMessage(item);

    try {
      await navigator.clipboard.writeText(message);
      setShareMessage("WhatsApp-ready route message copied.");
    } catch {
      const textArea = document.createElement("textarea");
      textArea.value = message;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      setShareMessage("WhatsApp-ready route message copied.");
    }

    setTimeout(() => setShareMessage(""), 2400);
  }

  function getJourneyConfidence(item) {
    const score = Number(item.score || 0);
    const transfers = typeof getRecommendationTransfers === "function"
      ? getRecommendationTransfers(item)
      : 0;

    const verifiedFare = typeof hasVerifiedFare === "function"
      ? hasVerifiedFare(item)
      : Boolean(item.fare?.estimated_fare || item.fare?.estimated_after_split);

    const risk = typeof getRouteRisk === "function"
      ? getRouteRisk(item)
      : { level: "medium" };

    let points = 0;

    if (score >= 850) points += 35;
    else if (score >= 750) points += 25;
    else if (score >= 650) points += 15;
    else points += 5;

    if (verifiedFare) points += 25;
    else points += 5;

    if (risk.level === "low") points += 25;
    else if (risk.level === "medium") points += 12;
    else points += 3;

    if (transfers === 0) points += 15;
    else if (transfers === 1) points += 10;
    else points += 4;

    if (points >= 80) {
      return {
        level: "high",
        label: "High confidence",
        reason: "Strong score, safer route, better fare coverage",
      };
    }

    if (points >= 55) {
      return {
        level: "medium",
        label: "Medium confidence",
        reason: "Good route but needs manual checking",
      };
    }

    return {
      level: "low",
      label: "Low confidence",
      reason: "Check timing, fare and transfer risk before booking",
    };
  }

  function getBestPickRouteKey(item) {
    if (typeof getCompareRouteKey === "function") {
      return getCompareRouteKey(item);
    }

    if (typeof getFavoriteRouteKey === "function") {
      return getFavoriteRouteKey(item);
    }

    const data = item.data || {};

    if (item.type === "direct") {
      return `best-direct-${source}-${destination}-${data.train_no}`;
    }

    if (item.type === "one_transfer") {
      return `best-transfer-${source}-${destination}-${data.first_train}-${data.transfer_station}-${data.second_train}`;
    }

    if (item.type === "multi_transfer") {
      const preview = data.route_preview?.join("-") || data.summary || "";
      const legs = data.train_legs?.map((leg) => leg.train_no).join("-") || "";
      return `best-smart-${source}-${destination}-${preview}-${legs}`;
    }

    return `best-${source}-${destination}-${getRecommendationTitle(item)}-${item.score || 0}`;
  }

  function getBestPickRoute() {
    const visibleList = Array.isArray(recommendations) ? recommendations : [];

    if (!visibleList.length) return null;

    return visibleList.reduce((best, item) => {
      const bestScore = Number(best?.score || 0);
      const itemScore = Number(item?.score || 0);

      if (itemScore > bestScore) return item;

      if (itemScore === bestScore) {
        const bestDuration = typeof getRecommendationDuration === "function"
          ? getRecommendationDuration(best)
          : 9999;

        const itemDuration = typeof getRecommendationDuration === "function"
          ? getRecommendationDuration(item)
          : 9999;

        if (itemDuration < bestDuration) return item;
      }

      return best;
    }, visibleList[0]);
  }

  function isBestPickRoute(item) {
    const bestPick = getBestPickRoute();

    if (!bestPick) return false;

    return getBestPickRouteKey(bestPick) === getBestPickRouteKey(item);
  }

  function formatTimelineTime(value) {
    if (!value || value === "None" || value === "N/A") return "Time not available";
    return String(value);
  }

  function getRouteTimelineSteps(item) {
    const data = item.data || {};
    const steps = [];

    if (item.type === "direct") {
      steps.push({
        type: "start",
        title: source,
        meta: `Board ${data.train_no || "train"}${data.train_name ? " - " + data.train_name : ""}`,
        time: formatTimelineTime(data.departure || data.source_departure),
      });

      steps.push({
        type: "end",
        title: destination,
        meta: "Arrive at destination",
        time: formatTimelineTime(data.arrival || data.destination_arrival),
      });

      return steps;
    }

    if (item.type === "one_transfer") {
      const transfer = data.transfer_station || "Transfer station";

      steps.push({
        type: "start",
        title: source,
        meta: `Board ${data.first_train || "first train"}`,
        time: formatTimelineTime(data.source_departure || data.first_departure),
      });

      steps.push({
        type: "transfer",
        title: transfer,
        meta: `Change to ${data.second_train || "second train"}`,
        time: formatTimelineTime(data.transfer_arrival || data.first_arrival),
      });

      steps.push({
        type: "end",
        title: destination,
        meta: "Arrive at destination",
        time: formatTimelineTime(data.destination_arrival || data.second_arrival),
      });

      return steps;
    }

    if (item.type === "multi_transfer") {
      const legs = Array.isArray(data.train_legs) ? data.train_legs : [];

      if (legs.length) {
        legs.forEach((leg, index) => {
          const fromStation =
            leg.from ||
            leg.source ||
            leg.start_station ||
            leg.start ||
            data.route_preview?.[index] ||
            `Stop ${index + 1}`;

          const toStation =
            leg.to ||
            leg.destination ||
            leg.end_station ||
            leg.end ||
            data.route_preview?.[index + 1] ||
            `Stop ${index + 2}`;

          steps.push({
            type: index === 0 ? "start" : "transfer",
            title: fromStation,
            meta: `Board ${leg.train_no || leg.train || "train"}`,
            time: formatTimelineTime(leg.start_time || leg.departure),
          });

          if (index === legs.length - 1) {
            steps.push({
              type: "end",
              title: toStation,
              meta: "Arrive at destination",
              time: formatTimelineTime(leg.end_time || leg.arrival),
            });
          }
        });

        return steps;
      }

      const preview = Array.isArray(data.route_preview) ? data.route_preview : [];

      if (preview.length) {
        preview.forEach((station, index) => {
          steps.push({
            type: index === 0 ? "start" : index === preview.length - 1 ? "end" : "transfer",
            title: station,
            meta: index === 0 ? "Start journey" : index === preview.length - 1 ? "Arrive at destination" : "Transfer point",
            time: "Time not available",
          });
        });

        return steps;
      }
    }

    return [
      {
        type: "start",
        title: source,
        meta: "Start journey",
        time: "Time not available",
      },
      {
        type: "end",
        title: destination,
        meta: "Arrive at destination",
        time: "Time not available",
      },
    ];
  }

  function extractTransferWaitHours(item) {
    if (typeof getTransferWaitHours === "function") {
      return getTransferWaitHours(item);
    }

    const data = item.data || {};
    const values = [
      data.transfer_wait_hours,
      data.max_transfer_wait_hours,
      data.total_wait_hours,
      data.wait_hours,
      data.connection_wait_hours,
    ];

    for (const value of values) {
      const numeric = Number(value);

      if (!Number.isNaN(numeric) && numeric >= 0) {
        return numeric;
      }
    }

    return null;
  }

  function getTransferSafety(item) {
    const transfers = typeof getRecommendationTransfers === "function"
      ? getRecommendationTransfers(item)
      : item.type === "direct"
        ? 0
        : 1;

    if (transfers === 0) {
      return {
        level: "direct",
        label: "Direct route",
        detail: "No transfer risk",
      };
    }

    const wait = extractTransferWaitHours(item);

    if (wait === null) {
      return {
        level: "unknown",
        label: "Transfer wait unknown",
        detail: "Check connection timing before booking",
      };
    }

    if (wait < 1) {
      return {
        level: "tight",
        label: "Tight transfer",
        detail: `${wait} hr wait · missed-connection risk`,
      };
    }

    if (wait < 2) {
      return {
        level: "okay",
        label: "Okay transfer",
        detail: `${wait} hr wait · verify delay risk`,
      };
    }

    if (wait <= 4) {
      return {
        level: "comfortable",
        label: "Comfortable transfer",
        detail: `${wait} hrs wait · safer buffer`,
      };
    }

    return {
      level: "long",
      label: "Long transfer wait",
      detail: `${wait} hrs wait · may be uncomfortable`,
    };
  }

  function getSmartBookingChecklist(item) {
    const checks = [];
    const data = item.data || {};
    const fare = item.fare || {};
    const split = item.split_ticket || {};
    const hasFare = typeof hasVerifiedFare === "function"
      ? hasVerifiedFare(item)
      : Boolean(fare.estimated_fare || fare.estimated_after_split);

    const transfers = typeof getRecommendationTransfers === "function"
      ? getRecommendationTransfers(item)
      : item.type === "direct"
        ? 0
        : 1;

    const risk = typeof getRouteRisk === "function"
      ? getRouteRisk(item)
      : { level: "medium" };

    const transferSafety = typeof getTransferSafety === "function"
      ? getTransferSafety(item)
      : null;

    const duration = typeof getRecommendationDuration === "function"
      ? getRecommendationDuration(item)
      : 9999;

    checks.push({
      status: "must",
      title: "Verify on IRCTC before booking",
      detail: "Confirm train availability, fare, quota and class on the official booking flow.",
    });

    checks.push({
      status: hasFare ? "ok" : "warn",
      title: hasFare ? "Fare data available" : "Fare needs manual check",
      detail: hasFare
        ? "RailYatra has fare estimate/coverage for this option."
        : "Fare may be missing or estimated. Confirm actual price before payment.",
    });

    checks.push({
      status: transfers === 0 ? "ok" : transferSafety?.level === "tight" ? "danger" : "warn",
      title: transfers === 0 ? "No transfer risk" : "Check transfer buffer",
      detail: transfers === 0
        ? "Direct route, no missed-connection risk."
        : transferSafety?.detail || "Check arrival and next train departure gap carefully.",
    });

    checks.push({
      status: risk.level === "high" ? "danger" : risk.level === "medium" ? "warn" : "ok",
      title: risk.level === "high" ? "High journey risk" : "Journey risk check",
      detail: risk.label || "Review delay, transfer and fare reliability before booking.",
    });

    checks.push({
      status: duration === 9999 ? "warn" : "ok",
      title: "Duration check",
      detail: duration === 9999
        ? "Duration not clearly available. Verify timing manually."
        : `Estimated duration: ${duration} hrs.`,
    });

    if (split.recommended) {
      checks.push({
        status: "warn",
        title: "Split-ticket saving available",
        detail: `Possible saving: ₹${split.estimated_saving || 0}. Verify both legs before booking.`,
      });
    }

    if (data.running_days || data.days) {
      checks.push({
        status: "must",
        title: "Train running day",
        detail: `Check running days: ${data.running_days || data.days}.`,
      });
    } else {
      checks.push({
        status: "must",
        title: "Train running day",
        detail: "Confirm that this train runs on your selected journey date.",
      });
    }

    return checks.slice(0, 7);
  }

  function renderSmartBookingChecklist(item) {
    const checks = getSmartBookingChecklist(item);

    if (!checks.length) return null;

    return (
      <div className="booking-checklist-card">
        <div className="booking-checklist-heading">
          <span>Booking checklist</span>
          <strong>Before final payment</strong>
        </div>

        <div className="booking-checklist-list">
          {checks.map((check, index) => (
            <div
              className={`booking-checklist-row booking-checklist-${check.status}`}
              key={`${check.title}-${index}`}
            >
              <div className="booking-checklist-icon">
                {check.status === "ok" ? "✓" : check.status === "danger" ? "!" : check.status === "must" ? "•" : "?"}
              </div>

              <div>
                <strong>{check.title}</strong>
                <span>{check.detail}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  function renderTransferSafetyBadge(item) {
    const safety = getTransferSafety(item);

    return (
      <div className={`transfer-safety-badge transfer-safety-${safety.level}`}>
        <strong>{safety.label}</strong>
        <span>{safety.detail}</span>
      </div>
    );
  }

  function renderRouteTimeline(item) {
    const steps = getRouteTimelineSteps(item);

    if (!steps.length) return null;

    return (
      <div className="route-timeline-card">
        <div className="route-timeline-heading">
          <span>Journey timeline</span>
          <strong>{steps.length} step{steps.length > 1 ? "s" : ""}</strong>
        </div>

        <div className="route-timeline-list">
          {steps.map((step, index) => (
            <div
              className={`route-timeline-step route-timeline-${step.type}`}
              key={`${step.title}-${index}`}
            >
              <div className="route-timeline-dot">{index + 1}</div>

              <div>
                <strong>{step.title}</strong>
                <span>{step.meta}</span>
                <small>{step.time}</small>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  function renderBestPickBadge(item) {
    if (!isBestPickRoute(item)) return null;

    const confidence = typeof getJourneyConfidence === "function"
      ? getJourneyConfidence(item)
      : null;

    return (
      <div className="best-pick-badge">
        <strong>🏆 Best Pick</strong>
        <span>
          {confidence?.label
            ? `${confidence.label} · highest visible route score`
            : "Highest visible route score"}
        </span>
      </div>
    );
  }

  function renderConfidenceBadge(item) {
    const confidence = getJourneyConfidence(item);

    return (
      <div className={`confidence-badge confidence-${confidence.level}`}>
        <strong>{confidence.label}</strong>
        <span>{confidence.reason}</span>
      </div>
    );
  }

  function getSmartRouteWarnings() {
    const sourceList = Array.isArray(recommendations) ? recommendations : [];
    const baseList = Array.isArray(allRecommendations) ? allRecommendations : [];
    const warnings = [];

    if (!baseList.length) {
      return warnings;
    }

    if (!sourceList.length && baseList.length) {
      warnings.push({
        level: "high",
        title: "No route matches current filters",
        detail: "Try resetting filters, increasing max fare, lowering minimum score, or selecting All day departure.",
      });

      return warnings;
    }

    const unknownFareCount = sourceList.filter((item) =>
      typeof hasVerifiedFare === "function" ? !hasVerifiedFare(item) : false
    ).length;

    const highRiskCount = sourceList.filter((item) => {
      if (typeof getRouteRisk !== "function") return false;
      return getRouteRisk(item).level === "high";
    }).length;

    const multiTransferCount = sourceList.filter((item) => {
      if (typeof getRecommendationTransfers !== "function") return false;
      return getRecommendationTransfers(item) >= 2;
    }).length;

    const longWaitCount = sourceList.filter((item) => {
      if (typeof getTransferWaitHours !== "function") return false;
      const wait = getTransferWaitHours(item);
      return wait !== null && wait >= 4;
    }).length;

    if (unknownFareCount) {
      warnings.push({
        level: "medium",
        title: `${unknownFareCount} route${unknownFareCount > 1 ? "s" : ""} need fare verification`,
        detail: "Fare estimate may be missing or approximate. Verify on IRCTC before booking.",
      });
    }

    if (highRiskCount) {
      warnings.push({
        level: "high",
        title: `${highRiskCount} high-risk route${highRiskCount > 1 ? "s" : ""} found`,
        detail: "Check transfer buffer, delay risk, and train running status carefully.",
      });
    }

    if (multiTransferCount) {
      warnings.push({
        level: "medium",
        title: `${multiTransferCount} route${multiTransferCount > 1 ? "s have" : " has"} multiple transfers`,
        detail: "Multiple transfers can increase missed-connection risk.",
      });
    }

    if (longWaitCount) {
      warnings.push({
        level: "medium",
        title: `${longWaitCount} route${longWaitCount > 1 ? "s have" : " has"} long transfer wait`,
        detail: "Long waits can make the journey uncomfortable. Compare alternatives before choosing.",
      });
    }

    if (!warnings.length && sourceList.length) {
      warnings.push({
        level: "low",
        title: "Routes look stable",
        detail: "No major warning detected for the currently visible recommendations.",
      });
    }

    return warnings.slice(0, 4);
  }

  function mapHealthPayloadToApiStatus(payload, statusCode = 200) {
    const graph = payload?.graph || {};
    const routing = payload?.routing || {};
    const api = payload?.api || {};
    const graphMeta =
      graph.nodes !== null && graph.nodes !== undefined && graph.edges !== null && graph.edges !== undefined
        ? `Graph: ${graph.nodes} stations/nodes, ${graph.edges} connections/edges`
        : graph.message || "Graph status not exposed";

    if (payload?.status === "ok") {
      return {
        state: "online",
        label: "Backend healthy",
        detail: routing.message || api.message || "RailYatra API and routing engine are connected.",
        meta: graphMeta,
      };
    }

    return {
      state: "warning",
      label: "Backend partially ready",
      detail: routing.message || `Health endpoint returned status ${statusCode}.`,
      meta: graphMeta,
    };
  }

  async function fetchBackendHealthStatus() {
    const response = await fetch(`${API_BASE}/health`);
    let payload = {};

    try {
      payload = await response.json();
    } catch {
      payload = {};
    }

    if (!response.ok) {
      return {
        state: "warning",
        label: "Backend health issue",
        detail: `Health endpoint returned status ${response.status}.`,
        meta: "Check backend terminal logs.",
      };
    }

    return mapHealthPayloadToApiStatus(payload, response.status);
  }

  function buildSearchErrorDetails(error, statusCode = null) {
    const message = error?.message || String(error || "Unknown error");
    const lowerMessage = message.toLowerCase();

    if (lowerMessage.includes("failed to fetch") || lowerMessage.includes("networkerror")) {
      return {
        title: "Backend is not reachable",
        detail: "Frontend could not connect to RailYatra API. Start backend server and retry.",
        fix: "cd ~/RailYatra/app && uvicorn backend.api.main:app --reload",
        statusCode,
      };
    }

    if (statusCode === 404) {
      return {
        title: "API endpoint not found",
        detail: "Frontend is calling an endpoint that backend does not expose yet.",
        fix: "Check backend routes in FastAPI /docs.",
        statusCode,
      };
    }

    if (statusCode && statusCode >= 500) {
      return {
        title: "Backend internal error",
        detail: "Backend crashed while processing this search. Check backend terminal traceback.",
        fix: "Read uvicorn terminal logs and fix the Python error shown there.",
        statusCode,
      };
    }

    if (statusCode && statusCode >= 400) {
      return {
        title: "Search request rejected",
        detail: message,
        fix: "Check source, destination, date, quota and class values.",
        statusCode,
      };
    }

    return {
      title: "Search failed",
      detail: message,
      fix: "Try again, or check frontend/backend terminal logs.",
      statusCode,
    };
  }

  function loosenStrictFilters() {
    if (typeof setMaxFare !== "undefined") setMaxFare("");
    if (typeof setMinScore !== "undefined") setMinScore("");
    if (typeof setMaxTransferWait !== "undefined") setMaxTransferWait("");
    if (typeof setHideUnknownFare !== "undefined") setHideUnknownFare(false);
    if (typeof setDepartureWindow !== "undefined") setDepartureWindow("all");

    setActiveFilter("all");
    setSortMode("best");
  }

  function getEmptyResultSuggestions() {
    const baseList = Array.isArray(allRecommendations) ? allRecommendations : [];
    const visibleList = Array.isArray(recommendations) ? recommendations : [];

    if (!baseList.length || visibleList.length) return [];

    const suggestions = [];

    if (typeof maxFare !== "undefined" && maxFare) {
      suggestions.push("Your max fare limit may be too low. Increase Max Fare or clear it.");
    }

    if (typeof minScore !== "undefined" && minScore) {
      suggestions.push("Minimum score may be too strict. Try lowering it.");
    }

    if (typeof maxTransferWait !== "undefined" && maxTransferWait) {
      suggestions.push("Max transfer wait may be hiding transfer routes. Increase wait limit.");
    }

    if (typeof departureWindow !== "undefined" && departureWindow !== "all") {
      suggestions.push("Departure time window is narrow. Try All day.");
    }

    if (typeof hideUnknownFare !== "undefined" && hideUnknownFare) {
      suggestions.push("Verified fare only is hiding routes with incomplete fare data.");
    }

    if (activeFilter !== "all") {
      suggestions.push("Route type filter is active. Try All recommendations.");
    }

    if (!suggestions.length) {
      suggestions.push("No visible journey after filters. Reset filters and search again.");
    }

    return suggestions.slice(0, 5);
  }

  function getSummaryFareValue(item) {
    if (typeof getRecommendationFare === "function") {
      const fare = getRecommendationFare(item);

      if (!Number.isNaN(Number(fare)) && Number(fare) > 0 && Number(fare) < 999999) {
        return Number(fare);
      }
    }

    const fare = item.fare || {};
    const data = item.data || {};
    const values = [
      fare.estimated_after_split,
      fare.estimated_fare,
      fare.total_fare,
      fare.fare,
      fare.amount,
      data.estimated_fare,
      data.fare,
    ];

    for (const value of values) {
      const numeric = Number(value);

      if (!Number.isNaN(numeric) && numeric > 0) {
        return numeric;
      }
    }

    return null;
  }

  function getSearchSummaryStats() {
    const baseList = Array.isArray(allRecommendations) ? allRecommendations : [];
    const visibleList = Array.isArray(recommendations) ? recommendations : [];

    if (!baseList.length) return null;

    const scoreValues = visibleList
      .map((item) => Number(item.score || 0))
      .filter((score) => score > 0);

    const fareValues = visibleList
      .map((item) => getSummaryFareValue(item))
      .filter((fare) => fare !== null);

    const durationValues = visibleList
      .map((item) =>
        typeof getRecommendationDuration === "function"
          ? getRecommendationDuration(item)
          : 9999
      )
      .filter((duration) => duration > 0 && duration < 9999);

    const directCount = visibleList.filter((item) =>
      typeof getRecommendationTransfers === "function"
        ? getRecommendationTransfers(item) === 0
        : item.type === "direct"
    ).length;

    const transferCount = visibleList.length - directCount;

    const averageScore = scoreValues.length
      ? Math.round(scoreValues.reduce((sum, score) => sum + score, 0) / scoreValues.length)
      : "N/A";

    const bestFare = fareValues.length ? Math.min(...fareValues) : null;
    const fastestDuration = durationValues.length ? Math.min(...durationValues) : null;

    return {
      total: baseList.length,
      visible: visibleList.length,
      hidden: Math.max(baseList.length - visibleList.length, 0),
      averageScore,
      bestFare,
      fastestDuration,
      directCount,
      transferCount,
    };
  }

  function isRouteSearchLoading() {
    return (
      (typeof loading !== "undefined" && loading) ||
      (typeof isLoading !== "undefined" && isLoading)
    );
  }

  function hasSearchResultPayload() {
    return Boolean(result);
  }

  function applyNoResultsSampleRoute() {
    setSource("PNBE");
    setDestination("NDLS");

    if (typeof setSearchValidation === "function") {
      setSearchValidation(null);
    }

    if (typeof setSearchErrorDetails === "function") {
      setSearchErrorDetails(null);
    }

    if (typeof setError === "function") {
      setError("");
    }

    if (typeof setShowAdvancedFilters === "function") {
      setShowAdvancedFilters(false);
    }

    if (typeof resetSearchFilters === "function") {
      resetSearchFilters();
    }
  }

  function renderCleanNoResultsCard() {
    const baseList = Array.isArray(allRecommendations) ? allRecommendations : [];
    const visibleList = Array.isArray(recommendations) ? recommendations : [];
    const loadingActive =
      (typeof loading !== "undefined" && loading) ||
      (typeof isLoading !== "undefined" && isLoading);

    if (loadingActive) return null;
    if (typeof searchValidation !== "undefined" && searchValidation) return null;
    if (typeof searchErrorDetails !== "undefined" && searchErrorDetails) return null;
    if (!hasSearchResultPayload()) return null;
    if (baseList.length || visibleList.length) return null;

    return (
      <div className="clean-no-results-card">
        <div className="clean-no-results-icon">🚆</div>

        <div>
          <span>No routes found</span>
          <strong>RailYatra could not find a route for this search</strong>
          <p>
            Try a popular test route, reset filters, or check if the backend data
            contains both station codes.
          </p>

          <div className="clean-no-results-tips">
            <small>Good test route: PNBE → NDLS</small>
            <small>Check station spellings and railway codes</small>
            <small>Try All train type and General quota</small>
          </div>
        </div>

        <div className="clean-no-results-actions">
          <button type="button" onClick={applyNoResultsSampleRoute}>
            Use PNBE → NDLS
          </button>

          <button
            type="button"
            onClick={() => {
              if (typeof resetSearchFilters === "function") {
                resetSearchFilters();
              }
            }}
          >
            Reset filters
          </button>
        </div>
      </div>
    );
  }

  function renderRouteSkeletonLoader() {
    if (!isRouteSearchLoading()) return null;

    return (
      <div className="route-skeleton-panel">
        <div className="route-skeleton-heading">
          <span>Searching routes</span>
          <strong>Finding smart RailYatra options...</strong>
        </div>

        <div className="route-skeleton-grid">
          {[1, 2, 3].map((item) => (
            <div className="route-skeleton-card" key={item}>
              <div className="skeleton-line skeleton-title"></div>
              <div className="skeleton-line skeleton-short"></div>

              <div className="skeleton-meta-row">
                <div className="skeleton-pill"></div>
                <div className="skeleton-pill"></div>
                <div className="skeleton-pill"></div>
              </div>

              <div className="skeleton-timeline">
                <div className="skeleton-dot"></div>
                <div className="skeleton-line"></div>
              </div>

              <div className="skeleton-timeline">
                <div className="skeleton-dot"></div>
                <div className="skeleton-line"></div>
              </div>

              <div className="skeleton-action-row">
                <div className="skeleton-button"></div>
                <div className="skeleton-button"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  function renderSearchSummaryStatsBar() {
    const stats = getSearchSummaryStats();

    if (!stats) return null;

    return (
      <div className="search-summary-stats">
        <div>
          <span>Total routes</span>
          <strong>{stats.total}</strong>
        </div>

        <div>
          <span>Visible</span>
          <strong>{stats.visible}</strong>
        </div>

        <div>
          <span>Hidden by filters</span>
          <strong>{stats.hidden}</strong>
        </div>

        <div>
          <span>Avg score</span>
          <strong>{stats.averageScore}</strong>
        </div>

        <div>
          <span>Best fare</span>
          <strong>{stats.bestFare ? `₹${stats.bestFare}` : "N/A"}</strong>
        </div>

        <div>
          <span>Fastest</span>
          <strong>{stats.fastestDuration ? `${stats.fastestDuration} hrs` : "N/A"}</strong>
        </div>

        <div>
          <span>Direct</span>
          <strong>{stats.directCount}</strong>
        </div>

        <div>
          <span>Transfer</span>
          <strong>{stats.transferCount}</strong>
        </div>
      </div>
    );
  }

  function getActiveFilterChips() {
    const chips = [];

    if (typeof journeyClass !== "undefined" && journeyClass !== "SL") {
      chips.push({
        key: "journeyClass",
        label: `Class: ${journeyClass}`,
        clear: () => setJourneyClass("SL"),
      });
    }

    if (typeof trainType !== "undefined" && trainType !== "All") {
      chips.push({
        key: "trainType",
        label: `Train: ${trainType}`,
        clear: () => setTrainType("All"),
      });
    }

    if (typeof journeyDate !== "undefined" && journeyDate) {
      chips.push({
        key: "journeyDate",
        label: `Date: ${journeyDate}`,
        clear: () => setJourneyDate(""),
      });
    }

    if (typeof quota !== "undefined" && quota !== "GN") {
      chips.push({
        key: "quota",
        label: `Quota: ${quota}`,
        clear: () => setQuota("GN"),
      });
    }

    if (typeof maxFare !== "undefined" && maxFare) {
      chips.push({
        key: "maxFare",
        label: `Max fare: ₹${maxFare}`,
        clear: () => setMaxFare(""),
      });
    }

    if (typeof departureWindow !== "undefined" && departureWindow !== "all") {
      chips.push({
        key: "departureWindow",
        label: `Departure: ${departureWindow}`,
        clear: () => setDepartureWindow("all"),
      });
    }

    if (typeof maxTransferWait !== "undefined" && maxTransferWait) {
      chips.push({
        key: "maxTransferWait",
        label: `Wait ≤ ${maxTransferWait} hrs`,
        clear: () => setMaxTransferWait(""),
      });
    }

    if (typeof minScore !== "undefined" && minScore) {
      chips.push({
        key: "minScore",
        label: `Score ≥ ${minScore}`,
        clear: () => setMinScore(""),
      });
    }

    if (typeof hideUnknownFare !== "undefined" && hideUnknownFare) {
      chips.push({
        key: "hideUnknownFare",
        label: "Verified fare only",
        clear: () => setHideUnknownFare(false),
      });
    }

    if (typeof activeFilter !== "undefined" && activeFilter !== "all") {
      chips.push({
        key: "activeFilter",
        label: `Route filter: ${activeFilter}`,
        clear: () => setActiveFilter("all"),
      });
    }

    if (typeof sortMode !== "undefined" && sortMode !== "best") {
      chips.push({
        key: "sortMode",
        label: `Sort: ${sortMode}`,
        clear: () => setSortMode("best"),
      });
    }

    return chips;
  }

  function clearAllActiveFilterChips() {
    const chips = getActiveFilterChips();
    chips.forEach((chip) => chip.clear());

    if (typeof setExpandedCard !== "undefined") {
      setExpandedCard(null);
    }
  }

  function renderActiveFilterChipsBar() {
    const chips = getActiveFilterChips();

    if (!chips.length) return null;

    return (
      <div className="active-filter-chips-bar">
        <div className="active-filter-chips-heading">
          <span>Active filters</span>
          <strong>{chips.length} active</strong>
        </div>

        <div className="active-filter-chips-list">
          {chips.map((chip) => (
            <button
              type="button"
              className="active-filter-chip"
              key={chip.key}
              onClick={chip.clear}
              title="Click to clear this filter"
            >
              {chip.label}
              <span>×</span>
            </button>
          ))}

          <button
            type="button"
            className="active-filter-chip clear-all-filter-chip"
            onClick={clearAllActiveFilterChips}
          >
            Clear all
          </button>
        </div>
      </div>
    );
  }

  function renderEmptyResultsSuggestionPanel() {
    const suggestions = getEmptyResultSuggestions();

    if (!suggestions.length) return null;

    return (
      <div className="empty-suggestion-panel">
        <div>
          <span>No visible results</span>
          <strong>Filters are probably too strict</strong>
          <p>RailYatra found routes, but current filters are hiding them.</p>

          <ul>
            {suggestions.map((suggestion) => (
              <li key={suggestion}>{suggestion}</li>
            ))}
          </ul>
        </div>

        <div className="empty-suggestion-actions">
          <button type="button" onClick={loosenStrictFilters}>
            Loosen filters
          </button>

          <button
            type="button"
            onClick={() => {
              if (typeof resetSearchFilters === "function") {
                resetSearchFilters();
              } else {
                loosenStrictFilters();
              }
            }}
          >
            Reset filters
          </button>
        </div>
      </div>
    );
  }

  function getStationInputCode(value) {
    const raw = String(value || "").trim();

    if (!raw) return "";

    if (typeof cleanStation === "function") {
      const cleaned = cleanStation(raw);

      if (cleaned) {
        return String(cleaned).trim().toUpperCase();
      }
    }

    const bracketMatch = raw.match(/\(([A-Z]{2,5})\)/i);

    if (bracketMatch) {
      return bracketMatch[1].toUpperCase();
    }

    const dashParts = raw.split("-");
    const firstPart = dashParts[0]?.trim();

    if (/^[A-Z]{2,5}$/i.test(firstPart)) {
      return firstPart.toUpperCase();
    }

    return raw.toUpperCase();
  }

  function validateSearchFormValues() {
    const fromCode = getStationInputCode(source);
    const toCode = getStationInputCode(destination);

    if (!fromCode && !toCode) {
      return {
        title: "Enter source and destination",
        detail: "Please add both station codes before searching.",
        action: "Example: PNBE to NDLS",
      };
    }

    if (!fromCode) {
      return {
        title: "Source station missing",
        detail: "Please enter the starting station.",
        action: "Example source: PNBE",
      };
    }

    if (!toCode) {
      return {
        title: "Destination station missing",
        detail: "Please enter the destination station.",
        action: "Example destination: NDLS",
      };
    }

    if (fromCode === toCode) {
      return {
        title: "Source and destination are same",
        detail: "Choose two different stations for route search.",
        action: "Example: PNBE to NDLS",
      };
    }

    if (!/^[A-Z]{2,5}$/.test(fromCode)) {
      return {
        title: "Source station format looks wrong",
        detail: "Use Indian Railway station code format with 2 to 5 letters.",
        action: `Current source: ${source}`,
      };
    }

    if (!/^[A-Z]{2,5}$/.test(toCode)) {
      return {
        title: "Destination station format looks wrong",
        detail: "Use Indian Railway station code format with 2 to 5 letters.",
        action: `Current destination: ${destination}`,
      };
    }

    return null;
  }

  function applySampleSearch() {
    setSource("PNBE");
    setDestination("NDLS");
    setSearchValidation(null);
  }

  function swapValidationStations() {
    const oldSource = source;
    setSource(destination);
    setDestination(oldSource);
    setSearchValidation(null);
  }

  function applyStationHelperRoute(from, to) {
    setSource(from);
    setDestination(to);

    if (typeof setSearchValidation === "function") {
      setSearchValidation(null);
    }

    if (typeof setSearchErrorDetails === "function") {
      setSearchErrorDetails(null);
    }

    if (typeof setError === "function") {
      setError("");
    }
  }

  function renderStationCodeHelperPanel() {
    const popularStations = [
      { code: "PNBE", name: "Patna Junction" },
      { code: "NDLS", name: "New Delhi" },
      { code: "DDU", name: "Pt. Deen Dayal Upadhyaya" },
      { code: "MGS", name: "Mughalsarai legacy code" },
      { code: "CNB", name: "Kanpur Central" },
      { code: "PRYJ", name: "Prayagraj Junction" },
      { code: "BSB", name: "Varanasi Junction" },
      { code: "GAYA", name: "Gaya Junction" },
    ];

    const popularRoutes = [
      { from: "PNBE", to: "NDLS", label: "Patna → Delhi" },
      { from: "NDLS", to: "PNBE", label: "Delhi → Patna" },
      { from: "PNBE", to: "DDU", label: "Patna → DDU" },
      { from: "CNB", to: "PNBE", label: "Kanpur → Patna" },
    ];

    return (
      <div className="station-code-helper-panel">
        <div className="station-code-helper-heading">
          <div>
            <span>Station code helper</span>
            <strong>Common RailYatra test codes</strong>
          </div>
        </div>

        <div className="station-code-grid">
          {popularStations.map((station) => (
            <button
              type="button"
              className="station-code-chip"
              key={station.code}
              onClick={() => {
                if (!source) {
                  setSource(station.code);
                } else {
                  setDestination(station.code);
                }
              }}
              title={station.name}
            >
              <strong>{station.code}</strong>
              <span>{station.name}</span>
            </button>
          ))}
        </div>

        <div className="popular-route-row">
          {popularRoutes.map((route) => (
            <button
              type="button"
              key={`${route.from}-${route.to}`}
              onClick={() => applyStationHelperRoute(route.from, route.to)}
            >
              {route.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

  function renderSearchValidationPanel() {
    if (!searchValidation) return null;

    return (
      <div className="search-validation-panel">
        <div>
          <span>Search validation</span>
          <strong>{searchValidation.title}</strong>
          <p>{searchValidation.detail}</p>
          <small>{searchValidation.action}</small>
        </div>

        <div className="search-validation-actions">
          <button type="button" onClick={applySampleSearch}>
            Use PNBE → NDLS
          </button>

          <button type="button" onClick={swapValidationStations}>
            Swap stations
          </button>

          <button type="button" onClick={() => setSearchValidation(null)}>
            Dismiss
          </button>
        </div>
      </div>
    );
  }

  function renderSearchErrorPanel() {
    if (!searchErrorDetails) return null;

    return (
      <div className="search-error-panel">
        <div>
          <span>Search error</span>
          <strong>{searchErrorDetails.title}</strong>
          <p>{searchErrorDetails.detail}</p>

          {searchErrorDetails.statusCode ? (
            <small>HTTP status: {searchErrorDetails.statusCode}</small>
          ) : null}

          <code>{searchErrorDetails.fix}</code>
        </div>

        <button type="button" onClick={handleSearch}>
          Retry search
        </button>
      </div>
    );
  }

  function renderBackendHealthCard() {
    const statusClass = `backend-health-card backend-health-${apiStatus.state}`;

    return (
      <div className={statusClass}>
        <div>
          <span>API health</span>
          <strong>{apiStatus.label}</strong>
          <p>{apiStatus.detail}</p>
          {apiStatus.meta ? <small>{apiStatus.meta}</small> : null}
        </div>

        <button
          type="button"
          onClick={async () => {
            setApiStatus({
              state: "checking",
              label: "Checking /health",
              detail: "Testing RailYatra health endpoint...",
              meta: "",
            });

            try {
              const nextStatus = await fetchBackendHealthStatus();
              setApiStatus(nextStatus);
            } catch {
              setApiStatus({
                state: "offline",
                label: "Backend offline",
                detail: "Start backend with uvicorn backend.api.main:app --reload",
                meta: "Then click Recheck.",
              });
            }
          }}
        >
          Recheck
        </button>
      </div>
    );
  }

  function renderSmartWarningsPanel() {
    const warnings = getSmartRouteWarnings();

    if (!warnings.length) return null;

    return (
      <div className="smart-warnings-panel">
        <div className="smart-warnings-heading">
          <span>Smart alerts</span>
          <strong>Before you book</strong>
        </div>

        <div className="smart-warnings-list">
          {warnings.map((warning, index) => (
            <div
              className={`smart-warning-card smart-warning-${warning.level}`}
              key={`${warning.title}-${index}`}
            >
              <strong>{warning.title}</strong>
              <span>{warning.detail}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  function renderShareButton(item) {
    return (
      <button
        type="button"
        className="share-journey-btn whatsapp-share-btn"
        onClick={() => shareRouteToClipboard(item)}
      >
        Copy WhatsApp message
      </button>
    );
  }

  function buildRecommendationReportText() {
    const lines = [];

    lines.push("RailYatra Route Comparison Report");
    lines.push("=================================");
    lines.push(`Route: ${source} → ${destination}`);
    lines.push(`Class: ${journeyClass}`);
    if (maxFare) lines.push(`Max fare: ₹${maxFare}`);
    lines.push(`Quota: ${quota}`);
    lines.push(`Journey date: ${journeyDate || "Not selected"}`);
    lines.push(`Train type: ${trainType}`);
    lines.push(`Filter: ${activeFilter}`);
    if (activeFilter === "low_risk") lines.push("Low risk journeys only");
    lines.push(`Sort: ${sortMode}`);
    lines.push(`Verified fare only: ${hideUnknownFare ? "Yes" : "No"}`);
    if (minScore) lines.push(`Minimum score: ${minScore}`);
    if (maxTransferWait) lines.push(`Max transfer wait: ${maxTransferWait} hrs`);
    lines.push(`Departure window: ${departureWindow}`);
    if (sortMode === "cheapest") lines.push("Lowest fare sort enabled");
    lines.push(`Total visible options: ${recommendations.length}`);

    if (fareVerificationSummary?.total) {
      lines.push(
        `Fare verification: ${fareVerificationSummary.verified}/${fareVerificationSummary.total} fully verified`
      );
      lines.push(
        `Fare coverage score: ${fareVerificationSummary.coveragePercent}%`
      );
    }

    lines.push("");

    recommendations.forEach((item, index) => {
      const data = item.data || {};
      const fare = item.fare || {};
      const split = item.split_ticket || {};
      const coverage = item.fare_coverage || {};
      const duration = getRecommendationDuration(item);
      const transfers = getRecommendationTransfers(item);

      lines.push(`${index + 1}. ${getRecommendationTitle(item)}`);
      lines.push("---------------------------------");
      lines.push(`Type: ${item.label || item.type}`);
      lines.push(`Score: ${item.score}`);
      lines.push(`Duration: ${duration === 9999 ? "N/A" : `${duration} hrs`}`);
      lines.push(`Transfers: ${transfers === 0 ? "No transfer" : transfers}`);

      if (fare.estimated_fare) {
        lines.push(`Fare: ₹${fare.estimated_fare}`);
        lines.push(
          `Fare source: ${
            fare.fare_source === "fare_table" ? "Verified fare table" : "Estimate"
          }`
        );
      }

      if (coverage.label) {
        lines.push(`Fare coverage: ${coverage.label}`);
      }

      if (split.recommended) {
        lines.push(`Split-ticket saving: ₹${split.estimated_saving}`);
        lines.push(`Split strategy: ${split.strategy}`);
      }

      if (item.type === "direct") {
        lines.push(`Train: ${data.train_no} - ${data.train_name}`);
        lines.push(`Departure: ${safeValue(data.departure)}`);
        lines.push(`Arrival: ${safeValue(data.arrival)}`);
      }

      if (item.type === "one_transfer") {
        lines.push(`First train: ${data.first_train} - ${data.first_train_name}`);
        lines.push(`Transfer at: ${data.transfer_station}`);
        lines.push(`Second train: ${data.second_train} - ${data.second_train_name}`);
        lines.push(`Wait time: ${safeValue(data.transfer_wait_hours)} hrs`);
      }

      if (item.type === "multi_transfer" && data.train_legs?.length) {
        lines.push("Train legs:");

        data.train_legs.forEach((leg, legIndex) => {
          lines.push(
            `${legIndex + 1}. ${leg.from} → ${leg.to} by ${leg.train_no} ${leg.train_name || ""}`
          );
        });
      }

      lines.push("");
    });

    lines.push("=================================");
    lines.push("Generated by RailYatra");

    return lines.join("\n");
  }

  async function copyRecommendationReport() {
    const text = buildRecommendationReportText();

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      setShareMessage("Full route comparison report copied.");
      setTimeout(() => setShareMessage(""), 2500);
    } catch (err) {
      setShareMessage("Could not copy route comparison report.");
      setTimeout(() => setShareMessage(""), 2500);
    }
  }

  function renderReportExportButton() {
    if (!recommendations.length) return null;

    return (
      <div className="report-export-box">
        <div>
          <span>Route comparison export</span>
          <strong>Copy all visible recommendations as one report</strong>
        </div>

        <div className="report-export-actions">
          <button type="button" onClick={copyRecommendationReport}>
            Copy full report
          </button>

          <button type="button" onClick={printRecommendationReport}>
            Print / Save PDF
          </button>
        </div>
      </div>
    );
  }

  function printRecommendationReport() {
    window.print();
  }

  function renderPrintableReport() {
    if (!recommendations.length) return null;

    return (
      <div className="print-report">
        <div className="print-report-header">
          <h1>RailYatra Route Comparison Report</h1>
          <p>{source} → {destination}</p>
        </div>

        <div className="print-report-summary">
          <div>
            <span>Total options</span>
            <strong>{recommendations.length}</strong>
          </div>

          <div>
            <span>Filter</span>
            <strong>{activeFilter}</strong>
          </div>

          <div>
            <span>Sort</span>
            <strong>{sortMode}</strong>
          </div>

          <div>
            <span>Quota</span>
            <strong>{quota}</strong>
          </div>


          <div>
            <span>Fare coverage</span>
            <strong>{fareVerificationSummary.coveragePercent}%</strong>
          </div>
        </div>

        {recommendations.map((item, index) => {
          const data = item.data || {};
          const fare = item.fare || {};
          const split = item.split_ticket || {};
          const coverage = item.fare_coverage || {};
          const duration = getRecommendationDuration(item);
          const transfers = getRecommendationTransfers(item);

          return (
            <div className="print-route-card" key={`print-${index}`}>
              <h2>
                {index + 1}. {getRecommendationTitle(item)}
              </h2>

              <div className="print-route-grid">
                <span>Type</span>
                <strong>{item.label || item.type}</strong>

                <span>Score</span>
                <strong>{item.score}</strong>

                <span>Duration</span>
                <strong>{duration === 9999 ? "N/A" : `${duration} hrs`}</strong>

                <span>Transfers</span>
                <strong>{transfers === 0 ? "No transfer" : transfers}</strong>

                <span>Fare</span>
                <strong>
                  {fare.estimated_fare ? `₹${fare.estimated_fare}` : "N/A"}
                </strong>

                <span>Fare source</span>
                <strong>
                  {fare.fare_source === "fare_table"
                    ? "Verified fare table"
                    : "Estimate"}
                </strong>

                <span>Fare coverage</span>
                <strong>{coverage.label || "N/A"}</strong>

                <span>Split saving</span>
                <strong>
                  {split.recommended ? `₹${split.estimated_saving}` : "N/A"}
                </strong>
              </div>

              {item.type === "direct" && (
                <div className="print-route-note">
                  Train: {data.train_no} - {data.train_name} · Dep{" "}
                  {safeValue(data.departure)} · Arr {safeValue(data.arrival)}
                </div>
              )}

              {item.type === "one_transfer" && (
                <div className="print-route-note">
                  {data.first_train} → transfer at {data.transfer_station} →{" "}
                  {data.second_train} · Wait {safeValue(data.transfer_wait_hours)} hrs
                </div>
              )}

              {item.type === "multi_transfer" && data.train_legs?.length > 0 && (
                <div className="print-route-note">
                  {data.train_legs.map((leg, legIndex) => (
                    <div key={legIndex}>
                      {legIndex + 1}. {leg.from} → {leg.to} by {leg.train_no}{" "}
                      {leg.train_name || ""}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        <div className="print-footer">
          Generated by RailYatra
        </div>
      </div>
    );
  }

  function renderDirectCard(item, index) {
    const train = item.data;

    const cardId = `direct-${index}`;

    return (
      <div className="journey-card" key={cardId}>
        <div className="card-top">
          <span className="badge direct-badge">Direct</span>
          <strong>Score {item.score}</strong>
        </div>

        <h3>{train.train_no} — {train.train_name}</h3>

        <div className="journey-meta">
          <span>Dep {safeValue(train.departure)}</span>
          <span>Arr {safeValue(train.arrival)}</span>
          <span>{safeValue(train.duration_hours)} hrs</span>
          <span>{safeValue(train.stops)} stops</span>
        </div>

        {renderRouteTags(item)}
        {renderRiskBadge(item)}
        {renderBestPickBadge(item)}
        {renderRouteTimeline(item)}
        {renderTransferSafetyBadge(item)}
        {renderSmartBookingChecklist(item)}
        {renderConfidenceBadge(item)}
        {renderFareBox(item)}
        {renderFareCoverageMeter(item)}
        {renderSplitTicketBox(item)}
        {renderShareButton(item)}
        {renderFavoriteButton(item)}
        {renderCompareButton(item)}

        <button
          type="button"
          className="details-btn"
          onClick={() => toggleDetails(cardId)}
        >
          {expandedCard === cardId ? "Hide details" : "View details"}
        </button>

        {expandedCard === cardId && (
          <div className="details-panel">
            <div className="section-title">Why recommended</div>

            <ul>
              {train.reasons?.map((reason, i) => (
                <li key={i}>✓ {reason}</li>
              ))}
            </ul>

            <div className="detail-grid">
              <span>Train no</span>
              <strong>{train.train_no}</strong>

              <span>Train name</span>
              <strong>{train.train_name}</strong>

              <span>Departure</span>
              <strong>{safeValue(train.departure)}</strong>

              <span>Arrival</span>
              <strong>{safeValue(train.arrival)}</strong>

              <span>Duration</span>
              <strong>{safeValue(train.duration_hours)} hrs</strong>

              <span>Stops</span>
              <strong>{safeValue(train.stops)}</strong>
            </div>
          </div>
        )}
      </div>
    );
  }

  function renderTransferCard(item, index) {
    const route = item.data;

    const cardId = `transfer-${index}`;

    return (
      <div className="journey-card" key={cardId}>
        <div className="card-top">
          <span className="badge transfer-badge">One transfer</span>
          <strong>Score {item.score}</strong>
        </div>

        <h3>
          {route.first_train} + {route.second_train}
        </h3>

        <p className="muted">
          {route.first_train_name} → {route.second_train_name}
        </p>

        <div className="timeline">
          <div>
            <strong>{result.source}</strong>
            <span>{safeValue(route.source_departure)}</span>
          </div>

          <div>
            <strong>{route.transfer_station}</strong>
            <span>
              Wait {safeValue(route.transfer_wait_hours)} hrs ·{" "}
              {route.transfer_station_name}
            </span>
          </div>

          <div>
            <strong>{result.destination}</strong>
            <span>{safeValue(route.destination_arrival)}</span>
          </div>
        </div>

        <div className="journey-meta">
          <span>Duration {safeValue(route.total_duration_hours)} hrs</span>
          <span>{safeValue(route.total_stops)} stops</span>
          <span>Wait {safeValue(route.transfer_wait_hours)} hrs</span>
        </div>

        {renderRouteTags(item)}
        {renderRiskBadge(item)}
        {renderConfidenceBadge(item)}
        {renderFareBox(item)}
        {renderFareCoverageMeter(item)}
        {renderSplitTicketBox(item)}
        {renderShareButton(item)}
        {renderFavoriteButton(item)}
        {renderCompareButton(item)}

        <button
          type="button"
          className="details-btn"
          onClick={() => toggleDetails(cardId)}
        >
          {expandedCard === cardId ? "Hide details" : "View details"}
        </button>

        {expandedCard === cardId && (
          <div className="details-panel">
            <div className="section-title">Journey breakdown</div>

            <div className="detail-grid">
              <span>First train</span>
              <strong>{route.first_train} — {route.first_train_name}</strong>

              <span>Transfer station</span>
              <strong>{route.transfer_station} — {route.transfer_station_name}</strong>

              <span>Second train</span>
              <strong>{route.second_train} — {route.second_train_name}</strong>

              <span>First leg</span>
              <strong>{safeValue(route.first_leg_duration_hours)} hrs</strong>

              <span>Wait time</span>
              <strong>{safeValue(route.transfer_wait_hours)} hrs</strong>

              <span>Second leg</span>
              <strong>{safeValue(route.second_leg_duration_hours)} hrs</strong>
            </div>
          </div>
        )}
      </div>
    );
  }

  function renderSmartRouteCard(item, index) {
    const route = item.data;
    const firstLeg = route.train_legs?.[0];

    const cardId = `smart-${index}`;

    return (
      <div className="journey-card" key={cardId}>
        <div className="card-top">
          <span className="badge direct-badge">
            {route.transfers === 0 ? "Smart direct" : "Smart route"}
          </span>
          <strong>Score {item.score}</strong>
        </div>

        <h3>{route.summary}</h3>

        <p className="muted">
          {route.route_preview?.join(" → ")}
        </p>

        <div className="journey-meta">
          <span>{route.transfers} transfers</span>
          <span>{route.leg_count} train leg{route.leg_count > 1 ? "s" : ""}</span>
          <span>{route.total_stops} stops</span>
          <span>{safeValue(route.total_duration_hours)} hrs</span>
        </div>

        {renderRouteTags(item)}
        {renderRiskBadge(item)}
        {renderConfidenceBadge(item)}
        {renderFareBox(item)}
        {renderFareCoverageMeter(item)}
        {renderSplitTicketBox(item)}
        {renderShareButton(item)}
        {renderFavoriteButton(item)}
        {renderCompareButton(item)}

        {firstLeg && (
          <div className="timeline">
            <div>
              <strong>{firstLeg.from}</strong>
              <span>{safeValue(firstLeg.start_time)}</span>
            </div>

            <div>
              <strong>{firstLeg.train_no}</strong>
              <span>
                {firstLeg.train_name || "Train"} · {firstLeg.stop_count} stops
              </span>
            </div>

            <div>
              <strong>{firstLeg.to}</strong>
              <span>{safeValue(firstLeg.end_time)}</span>
            </div>
          </div>
        )}

        <button
          type="button"
          className="details-btn"
          onClick={() => toggleDetails(cardId)}
        >
          {expandedCard === cardId ? "Hide details" : "View details"}
        </button>

        {expandedCard === cardId && (
          <div className="details-panel">
            {route.reasons?.length > 0 && (
              <>
                <div className="section-title">Why recommended</div>
                <ul>
                  {route.reasons.map((reason, i) => (
                    <li key={i}>✓ {reason}</li>
                  ))}
                </ul>
              </>
            )}

            <div className="section-title">Train legs</div>
            <ul>
              {route.train_legs?.map((leg, i) => (
                <li key={i}>
                  ✓ {leg.from} → {leg.to} by {leg.train_no} ·{" "}
                  {leg.train_name || "Train"} · {safeValue(leg.start_time)} →{" "}
                  {safeValue(leg.end_time)} · {safeValue(leg.duration_hours)} hrs
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  function renderRecommendation(item, index) {
    if (item.type === "direct") {
      return renderDirectCard(item, index);
    }

    if (item.type === "one_transfer") {
      return renderTransferCard(item, index);
    }

    if (item.type === "multi_transfer") {
      return renderSmartRouteCard(item, index);
    }

    return null;
  }

  return (
    <div className="page">
      <nav className="navbar">
        <div className="brand">🚆 RailYatra</div>
        <div className="nav-pill">MVP Beta</div>
      </nav>

      <main className="app">
        <PublicDemoWarningBanner />
      <PublicDemoHero />
        <PublicDemoInternalPanel title="Staging data health" description="Backend data/status check for demo verification.">
        <Phase3StagingCard />
      </PublicDemoInternalPanel>
        <Phase3DirectPreview />
        <Phase3RouteSearchPreview />
        <div id="recommendations-preview" className="recommendations-preview-section">
        <PublicRecommendationIntro />
        <Phase4RecommendationPreview />
      </div>
        <PublicDemoInternalPanel title="Product status flags" description="Confirms live booking/payment/PNR are not enabled.">
        <Phase5ProductStatusPanel />
      </PublicDemoInternalPanel>
        <Phase5BetaChecklistPanel />
        <header className="hero">
          <div className="pill">Smart Railway Planner</div>
          <h1>Find the best train journey</h1>
          <p>
            Search direct trains, transfer routes, duration, score and smart
            recommendations.
          </p>
        </header>

        <form id="main-search" className="search-card" onSubmit={searchJourney}>
          <div className="field">
            <label>From</label>
            <input
              value={source}
              onChange={(e) => handleMainStationInputChange(e, "source")}
              onFocus={() => handleMainStationInputFocus("source")}
              onKeyUp={(e) => handleMainStationInputKeyUp(e, "source")}
              placeholder="PNBE or Patna"
            />

            {sourceSuggestions.length > 0 && (
              <div className="suggestions-panel">
                {sourceSuggestions.map((station, index) => (
                  <button
                    type="button"
                    className="suggestion-item"
                    key={index}
                    onClick={() => {
                      setSource(getStationCode(station));
                      setSourceSuggestions([]);
                    }}
                  >
                    <strong>{getStationCode(station)}</strong>
                    <span>{getStationName(station)}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button type="button" className="swap-btn" onClick={swapStations}>
            ⇅
          </button>

          <div className="field">
            <label>To</label>
            <input
              value={destination}
              onChange={(e) => handleMainStationInputChange(e, "destination")}
              onFocus={() => handleMainStationInputFocus("destination")}
              onKeyUp={(e) => handleMainStationInputKeyUp(e, "destination")}
              placeholder="NDLS or Delhi"
            />

            {destinationSuggestions.length > 0 && (
              <div className="suggestions-panel">
                {destinationSuggestions.map((station, index) => (
                  <button
                    type="button"
                    className="suggestion-item"
                    key={index}
                    onClick={() => {
                      setDestination(getStationCode(station));
                      setDestinationSuggestions([]);
                    }}
                  >
                    <strong>{getStationCode(station)}</strong>
                    <span>{getStationName(station)}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="field">
            <label>Class</label>
            <select
              value={journeyClass}
              onChange={(e) => setJourneyClass(e.target.value)}
            >
              <option value="SL">Sleeper - SL</option>
              <option value="3A">AC 3 Tier - 3A</option>
              <option value="2A">AC 2 Tier - 2A</option>
              <option value="1A">AC First Class - 1A</option>
              <option value="CC">Chair Car - CC</option>
              <option value="2S">Second Sitting - 2S</option>
            </select>
          </div>

          <div className="advanced-filter-toggle-row">
            <button
              type="button"
              className="advanced-filter-toggle"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            >
              {showAdvancedFilters
                ? "Hide advanced filters"
                : `Show advanced filters${getAdvancedFilterCount() ? ` (${getAdvancedFilterCount()} active)` : ""}`}
            </button>
          </div>

          <div className={showAdvancedFilters ? "field advanced-filter" : "field advanced-filter advanced-filter-hidden"}>
            <label>Train Type</label>
            <select
              value={trainType}
              onChange={(e) => setTrainType(e.target.value)}
            >
              <option value="All">All</option>
              <option value="Rajdhani">Rajdhani</option>
              <option value="Superfast">Superfast</option>
              <option value="Express">Express</option>
              <option value="Direct only">Direct only</option>
            </select>
          </div>

          <div className="field">
            <label>Journey Date</label>
            <input
              type="date"
              value={journeyDate}
              onChange={(e) => setJourneyDate(e.target.value)}
            />
          </div>


          <div className={showAdvancedFilters ? "field advanced-filter" : "field advanced-filter advanced-filter-hidden"}>
            <label>Quota</label>
            <select
              value={quota}
              onChange={(e) => setQuota(e.target.value)}
            >
              <option value="GN">General - GN</option>
              <option value="TQ">Tatkal - TQ</option>
              <option value="LD">Ladies - LD</option>
              <option value="SS">Senior Citizen - SS</option>
            </select>
          </div>

          <div className={showAdvancedFilters ? "field advanced-filter" : "field advanced-filter advanced-filter-hidden"}>
            <label>Max Fare</label>
            <input
              type="number"
              min="1"
              value={maxFare}
              onChange={(e) => setMaxFare(e.target.value)}
              placeholder="Max ₹"
            />
          </div>

          <button
            type="button"
            className="search-btn secondary"
            onClick={resetSearchFilters}
          >
            Reset Filters
          </button>

          <div className={showAdvancedFilters ? "field advanced-filter" : "field advanced-filter advanced-filter-hidden"}>
            <label>Departure Time</label>
            <select
              value={departureWindow}
              onChange={(e) => setDepartureWindow(e.target.value)}
            >
              <option value="all">All day</option>
              <option value="morning">Morning: 5 AM - 12 PM</option>
              <option value="afternoon">Afternoon: 12 PM - 5 PM</option>
              <option value="evening">Evening: 5 PM - 9 PM</option>
              <option value="night">Night: 9 PM - 5 AM</option>
            </select>
          </div>

          <div className={showAdvancedFilters ? "field advanced-filter" : "field advanced-filter advanced-filter-hidden"}>
            <label>Max Transfer Wait</label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={maxTransferWait}
              onChange={(e) => setMaxTransferWait(e.target.value)}
              placeholder="Hours"
            />
          </div>

          <div className={showAdvancedFilters ? "field advanced-filter" : "field advanced-filter advanced-filter-hidden"}>
            <label>Minimum Score</label>
            <input
              type="number"
              min="1"
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
              placeholder="Example: 700"
            />
          </div>

          <div className={showAdvancedFilters ? "field checkbox-field advanced-filter" : "field checkbox-field advanced-filter advanced-filter-hidden"}>
            <label>Hide Unknown Fare</label>
            <label className="inline-check">
              <input
                type="checkbox"
                checked={hideUnknownFare}
                onChange={(e) => setHideUnknownFare(e.target.checked)}
              />
              Show only verified fare journeys
            </label>
          </div>

          <button type="submit" className="search-btn">
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

          {renderFareAdminPanel()}

        {renderFavoritesPanel()}

        {renderComparePanel()}

        {renderBackendHealthCard()}

        {renderActiveFilterChipsBar()}

        {renderStationCodeHelperPanel()}

        {renderSearchValidationPanel()}

        {renderSearchErrorPanel()}

        {renderEmptyResultsSuggestionPanel()}

        {renderSearchSummaryStatsBar()}

        {renderRouteSkeletonLoader()}

        {renderCleanNoResultsCard()}

        {renderSmartWarningsPanel()}

        {renderRecentSearchesPanel()}

        <div className="quick-routes">
          <button type="button" onClick={() => setQuickRoute("NDLS", "PNBE")}>
            NDLS → PNBE
          </button>
          <button type="button" onClick={() => setQuickRoute("PNBE", "NDLS")}>
            PNBE → NDLS
          </button>
          <button type="button" onClick={() => setQuickRoute("NDLS", "HWH")}>
            NDLS → HWH
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            Finding best journeys...
          </div>
        )}

        {result && (
          <section className="results">
            <h2>
              {result.source} → {result.destination}
            </h2>

            <p className="summary">
              Route exists: {result.route_exists ? "Yes" : "No"} · Direct:{" "}
              {result.direct_count} · One-transfer: {result.transfer_count} ·
              Smart routes: {result.multi_route_count || 0}
            </p>

            <div className="highlight-grid">
              <div className="highlight-card">
                <span>Best smart</span>
                <strong>
                  {bestSmart
                    ? bestSmart.data.summary
                    : "Not available"}
                </strong>
              </div>

              <div className="highlight-card">
                <span>Best direct</span>
                <strong>
                  {bestDirect
                    ? `${bestDirect.data.train_no} ${bestDirect.data.train_name}`
                    : "Not available"}
                </strong>
              </div>

              <div className="highlight-card">
                <span>Best transfer</span>
                <strong>
                  {bestTransfer
                    ? `${bestTransfer.data.first_train} + ${bestTransfer.data.second_train}`
                    : "Not available"}
                </strong>
              </div>

              <div className="highlight-card">
                <span>Total options</span>
                <strong>{result.total_recommendations || recommendations.length}</strong>
              </div>
            </div>

            {shareMessage && (
              <div className="share-message">{shareMessage}</div>
            )}

            {renderFareVerificationSummary()}

            <div className="comparison-grid">
              <div className="comparison-card">
                <span>🏆 Best overall</span>
                <strong>{getRecommendationTitle(result.best)}</strong>
                <p>{getRecommendationSubtext(result.best)}</p>
                {renderComparisonFareIndicator(result.best)}
              </div>

              <div className="comparison-card">
                <span>⚡ Fastest</span>
                <strong>{getRecommendationTitle(fastestOption)}</strong>
                <p>{getRecommendationSubtext(fastestOption)}</p>
                {renderComparisonFareIndicator(fastestOption)}
              </div>

              <div className="comparison-card">
                <span>🔁 Least transfers</span>
                <strong>{getRecommendationTitle(leastTransferOption)}</strong>
                <p>{getRecommendationSubtext(leastTransferOption)}</p>
                {renderComparisonFareIndicator(leastTransferOption)}
              </div>
            </div>

            {result.best && (
              <div className="best-box">
                <span>🏆 Best recommendation</span>
                <strong>{result.best.label}</strong>
              </div>
            )}

            <div className="filter-tabs">
              <button
                type="button"
                className={activeFilter === "all" ? "active" : ""}
                onClick={() => setActiveFilter("all")}
              >
                All
              </button>

              <button
                type="button"
                className={activeFilter === "smart" ? "active" : ""}
                onClick={() => setActiveFilter("smart")}
              >
                Smart
              </button>

              <button
                type="button"
                className={activeFilter === "low_risk" ? "active" : ""}
                onClick={() => setActiveFilter("low_risk")}
              >
                Low Risk
              </button>

              <button
                type="button"
                className={activeFilter === "direct" ? "active" : ""}
                onClick={() => setActiveFilter("direct")}
              >
                Direct
              </button>

              <button
                type="button"
                className={activeFilter === "transfer" ? "active" : ""}
                onClick={() => setActiveFilter("transfer")}
              >
                Transfer
              </button>

              <button
                type="button"
                className={activeFilter === "verified_fare" ? "active" : ""}
                onClick={() => setActiveFilter("verified_fare")}
              >
                Verified Fare
              </button>
            </div>

            <div className="sort-tabs">
              <span>Sort by</span>

              <button
                type="button"
                className={sortMode === "best" ? "active" : ""}
                onClick={() => setSortMode("best")}
              >
                Best
              </button>

              <button
                type="button"
                className={sortMode === "fastest" ? "active" : ""}
                onClick={() => setSortMode("fastest")}
              >
                Fastest
              </button>

              <button
                type="button"
                className={sortMode === "least_transfers" ? "active" : ""}
                onClick={() => setSortMode("least_transfers")}
              >
                Least Transfers
              </button>

              <button
                type="button"
                className={sortMode === "cheapest" ? "active" : ""}
                onClick={() => setSortMode("cheapest")}
              >
                Lowest Fare
              </button>
            </div>

            {renderPrintableReport()}

            {renderReportExportButton()}

            {recommendations.length === 0 && (
              <div className="empty-state">No journey found for this filter.</div>
            )}

            {recommendations.map((item, index) =>
              renderRecommendation(item, index)
            )}
          </section>
        )}
            <PublicDemoFooter />
</main>
    </div>
  );
}

export default App;
