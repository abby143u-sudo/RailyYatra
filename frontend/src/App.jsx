import { useMemo, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [source, setSource] = useState("PNBE");
  const [destination, setDestination] = useState("NDLS");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sourceSuggestions, setSourceSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [sortMode, setSortMode] = useState("best");
  const [expandedCard, setExpandedCard] = useState(null);
  const [shareMessage, setShareMessage] = useState("");
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

    return sorted;
  }, [allRecommendations, activeFilter, sortMode]);

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

  function cleanStation(value) {
    return value.trim().toUpperCase();
  }

  function swapStations() {
    setSource(destination);
    setDestination(source);
  }

  async function fetchStationSuggestions(value, setter) {
    const query = value.trim();

    if (query.length < 2) {
      setter([]);
      return;
    }

    try {
      const res = await fetch(API_BASE + "/stations?q=" + query + "&limit=8");

      if (!res.ok) return;

      const data = await res.json();
      setter(data.stations || []);
    } catch {
      setter([]);
    }
  }

  function getStationCode(station) {
    return station.station_code || station.code || station.id || "";
  }

  function getStationName(station) {
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
    setError("");
    setResult(null);
    setActiveFilter("all");
    setSortMode("best");
    setExpandedCard(null);

    try {
      const res = await fetch(
        API_BASE + "/search?source=" + from + "&destination=" + to + "&limit=10"
      );

      if (!res.ok) throw new Error("Search failed");

      const data = await res.json();
      setResult(data);
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

            <button type="submit" disabled={fareAdminLoading}>
                  Save verified fare
                </button>
              </form>
            </div>

            <div className="fare-admin-section">
              <h4>Importable CSV files</h4>

              {fareFiles.length === 0 && (
                <p>No CSV file found in app/data/raw.</p>
              )}

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

  function renderShareButton(item) {
    return (
      <button
        type="button"
        className="share-journey-btn"
        onClick={() => copyJourney(item)}
      >
        Copy journey
      </button>
    );
  }

  function buildRecommendationReportText() {
    const lines = [];

    lines.push("RailYatra Route Comparison Report");
    lines.push("=================================");
    lines.push(`Route: ${source} → ${destination}`);
    lines.push(`Class: ${journeyClass}`);
    lines.push(`Filter: ${activeFilter}`);
    lines.push(`Sort: ${sortMode}`);
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
        {renderFareBox(item)}
        {renderFareCoverageMeter(item)}
        {renderSplitTicketBox(item)}
        {renderShareButton(item)}

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
        {renderFareBox(item)}
        {renderFareCoverageMeter(item)}
        {renderSplitTicketBox(item)}
        {renderShareButton(item)}

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
        {renderFareBox(item)}
        {renderFareCoverageMeter(item)}
        {renderSplitTicketBox(item)}
        {renderShareButton(item)}

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
        <header className="hero">
          <div className="pill">Smart Railway Planner</div>
          <h1>Find the best train journey</h1>
          <p>
            Search direct trains, transfer routes, duration, score and smart
            recommendations.
          </p>
        </header>

        <form className="search-card" onSubmit={searchJourney}>
          <div className="field">
            <label>From</label>
            <input
              value={source}
              onChange={(e) => {
                const value = e.target.value.toUpperCase();
                setSource(value);
                fetchStationSuggestions(value, setSourceSuggestions);
              }}
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
              onChange={(e) => {
                const value = e.target.value.toUpperCase();
                setDestination(value);
                fetchStationSuggestions(value, setDestinationSuggestions);
              }}
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

          <button type="submit" className="search-btn">
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

          {renderFareAdminPanel()}

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
      </main>
    </div>
  );
}

export default App;
