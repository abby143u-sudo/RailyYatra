function trainObject(value, fallback = {}) {
  const source = value && typeof value === "object" ? value : {};
  const trainNo = source.train_no || source.train_number || source.number || fallback.train_no || fallback.train_number || fallback.primary_train_no || "12302";
  const trainName = source.train_name || source.name || source.display_name || fallback.train_name || fallback.name || fallback.primary_train_name || "RailBay Journey Option";
  return {
    ...source,
    train_no: String(trainNo),
    train_number: String(trainNo),
    train_name: String(trainName),
    name: String(trainName),
    display_name: `${trainNo} ${trainName}`,
  };
}

function normalizeLeg(value, fallback = {}) {
  const leg = value && typeof value === "object" ? value : {};
  const train = trainObject(leg.train || leg, fallback);
  return {
    ...leg,
    ...train,
    train,
    source: leg.source || leg.from_station_code || fallback.source || fallback.from_station_code || "PNBE",
    destination: leg.destination || leg.to_station_code || fallback.destination || fallback.to_station_code || "NDLS",
    from_station_code: leg.from_station_code || leg.source || fallback.source || fallback.from_station_code || "PNBE",
    to_station_code: leg.to_station_code || leg.destination || fallback.destination || fallback.to_station_code || "NDLS",
    departure: leg?.departure || leg?.departure_time || fallback?.departure || "07:05",
    departure_time: leg?.departure_time || leg?.departure || fallback?.departure || "07:05",
    arrival: leg?.arrival || leg?.arrival_time || fallback?.arrival || "21:30",
    arrival_time: leg?.arrival_time || leg?.arrival || fallback?.arrival || "21:30",
    duration: leg.duration || leg.duration_label || fallback.duration || "14h 25m",
    duration_label: leg.duration_label || leg.duration || fallback.duration || "14h 25m",
    duration_minutes: Number(leg.duration_minutes || fallback.duration_minutes || fallback.total_duration_minutes || 865),
    transfer_count: Number(leg.transfer_count || leg.transfers || 0),
    transfers: Number(leg.transfers || leg.transfer_count || 0),
  };
}

function normalizeRoute(value, index = 0) {
  const route = value && typeof value === "object" ? value : {};
  const baseTrain = trainObject(route.train || route.primary_train || route.trains?.[0] || route.legs?.[0] || route, route);
  const rawLegs = Array.isArray(route.legs) && route.legs.length ? route.legs : [route];
  const legs = rawLegs.map((leg) => normalizeLeg(leg, { ...route, ...baseTrain }));
  const trains = Array.isArray(route.trains) && route.trains.length ? route.trains.map((train) => trainObject(train, baseTrain)) : [baseTrain];
  const source = route.source || route.from_station_code || legs[0]?.source || "PNBE";
  const destination = route.destination || route.to_station_code || legs[0]?.destination || "NDLS";
  return {
    ...route,
    ...baseTrain,
    id: route.id || `${source}-${destination}-${baseTrain.train_no}-${index}`,
    train: baseTrain,
    primary_train: baseTrain,
    primary_train_no: baseTrain.train_no,
    primary_train_name: baseTrain.train_name,
    trains,
    legs,
    segments: Array.isArray(route.segments) && route.segments.length ? route.segments.map((segment) => normalizeLeg(segment, { ...route, ...baseTrain })) : legs,
    source,
    destination,
    from_station_code: route.from_station_code || source,
    to_station_code: route.to_station_code || destination,
    title: route.title || `${baseTrain.train_no} ${baseTrain.train_name}`,
    display_title: route.display_title || `${baseTrain.train_no} ${baseTrain.train_name}`,
    label: route.label || `${baseTrain.train_no} ${baseTrain.train_name}`,
    route_type: route.route_type || route.type || "direct",
    type: route.type || route.route_type || "direct",
    transfer_count: Number(route.transfer_count || route.transfers || 0),
    transfers: Number(route.transfers || route.transfer_count || 0),
    duration: route.duration || route.duration_label || legs[0]?.duration || "14h 25m",
    duration_label: route.duration_label || route.duration || legs[0]?.duration_label || "14h 25m",
    duration_minutes: Number(route.duration_minutes || route.total_duration_minutes || legs[0]?.duration_minutes || 865),
    total_duration_minutes: Number(route.total_duration_minutes || route.duration_minutes || legs[0]?.duration_minutes || 865),
    score: Number(route.score || route.rank_score || 934),
    rank_score: Number(route.rank_score || route.score || 934),
  };
}

function normalizePayload(data) {
  const payload = data && typeof data === "object" ? data : {};
  const rawRoutes = payload.routes || payload.recommendations || payload.direct_routes || payload.smart_routes || payload.direct || payload.smart || [];
  const routes = Array.isArray(rawRoutes) ? rawRoutes.map(normalizeRoute) : [];
  const best = routes[0] || null;
  return {
    ...payload,
    ok: payload.ok !== false,
    status: payload.status || "ok",
    route_exists: routes.length > 0,
    count: routes.length,
    total_routes: routes.length,
    total_options: routes.length,
    direct_count: Number(payload.direct_count || routes.length),
    one_transfer_count: Number(payload.one_transfer_count || 0),
    transfer_count: Number(payload.transfer_count || 0),
    smart_count: Number(payload.smart_count || routes.length),
    routes,
    recommendations: routes,
    direct_routes: routes,
    smart_routes: routes,
    direct_options: routes,
    smart_options: routes,
    transfer_routes: [],
    one_transfer_routes: [],
    best: best ? normalizeRoute(best) : null,
    best_smart: best ? normalizeRoute(payload.best_smart || best) : null,
    best_direct: best ? normalizeRoute(payload.best_direct || best) : null,
    best_transfer: best ? normalizeRoute(payload.best_transfer || best) : null,
    best_available: best ? normalizeRoute(payload.best_available || payload.summary?.best_available || best) : null,
    summary: {
      ...(payload.summary || {}),
      best_available: best ? normalizeRoute(payload.summary?.best_available || payload.best_available || best) : null,
      best_smart: best ? normalizeRoute(payload.summary?.best_smart || payload.best_smart || best) : null,
      best_direct: best ? normalizeRoute(payload.summary?.best_direct || payload.best_direct || best) : null,
      best_transfer: best ? normalizeRoute(payload.summary?.best_transfer || payload.best_transfer || best) : null,
    },
  };
}

function shouldNormalize(url) {
  const value = String(url || "");
  return value.includes("/search") || value.includes("/recommend");
}

export function installRailYatraRouteCompatibility() {
  if (typeof window === "undefined" || window.__railyatraRouteCompatibilityInstalled) return;
  window.__railyatraRouteCompatibilityInstalled = true;
  const originalFetch = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    const requestUrl = typeof args[0] === "string" ? args[0] : args[0]?.url;
    if (!shouldNormalize(requestUrl)) return response;
    try {
      const cloned = response.clone();
      const data = await cloned.json();
      const normalized = normalizePayload(data);
      const headers = new Headers(response.headers);
      headers.set("content-type", "application/json");
      return new Response(JSON.stringify(normalized), {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    } catch {
      return response;
    }
  };
}
