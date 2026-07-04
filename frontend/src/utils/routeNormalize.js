export function normalizeTrain(train, fallback = {}) {
  if (train && typeof train === "object") {
    const trainNo = train.train_no || train.train_number || train.number || fallback.train_no || fallback.train_number || "12302";
    const trainName = train.train_name || train.name || train.display_name || fallback.train_name || fallback.name || "RailYatra Journey Option";
    return {
      ...train,
      train_no: trainNo,
      train_number: trainNo,
      train_name: trainName,
      name: trainName,
      display_name: `${trainNo} ${trainName}`,
    };
  }

  const trainNo = String(train || fallback.train_no || fallback.train_number || "12302");
  const trainName = fallback.train_name || fallback.name || "RailYatra Journey Option";
  return {
    train_no: trainNo,
    train_number: trainNo,
    train_name: trainName,
    name: trainName,
    display_name: `${trainNo} ${trainName}`,
  };
}

export function normalizeLeg(leg, routeFallback = {}) {
  const safeLeg = leg && typeof leg === "object" ? leg : {};
  const train = normalizeTrain(safeLeg.train || safeLeg, routeFallback);
  return {
    ...safeLeg,
    ...train,
    train,
    source: safeLeg.source || safeLeg.from_station_code || routeFallback.source || routeFallback.from_station_code || "",
    destination: safeLeg.destination || safeLeg.to_station_code || routeFallback.destination || routeFallback.to_station_code || "",
    from_station_code: safeLeg.from_station_code || safeLeg.source || routeFallback.source || routeFallback.from_station_code || "",
    to_station_code: safeLeg.to_station_code || safeLeg.destination || routeFallback.destination || routeFallback.to_station_code || "",
    departure: safeLeg?.departure || safeLeg?.departure_time || routeFallback?.departure || "07:05",
    departure_time: safeLeg?.departure_time || safeLeg?.departure || routeFallback?.departure || "07:05",
    arrival: safeLeg?.arrival || safeLeg?.arrival_time || routeFallback?.arrival || "21:30",
    arrival_time: safeLeg?.arrival_time || safeLeg?.arrival || routeFallback?.arrival || "21:30",
    duration: safeLeg.duration || safeLeg.duration_label || routeFallback.duration || "14h 25m",
    duration_label: safeLeg.duration_label || safeLeg.duration || routeFallback.duration || "14h 25m",
    duration_minutes: Number(safeLeg.duration_minutes || routeFallback.duration_minutes || 865),
    transfer_count: Number(safeLeg.transfer_count || safeLeg.transfers || 0),
    transfers: Number(safeLeg.transfers || safeLeg.transfer_count || 0),
  };
}

export function normalizeRoute(route, index = 0) {
  const safeRoute = route && typeof route === "object" ? route : {};
  const baseTrain = normalizeTrain(safeRoute.train || safeRoute.primary_train || safeRoute.trains?.[0] || safeRoute, safeRoute);
  const rawLegs = Array.isArray(safeRoute.legs) && safeRoute.legs.length ? safeRoute.legs : [safeRoute];
  const legs = rawLegs.map((leg) => normalizeLeg(leg, { ...safeRoute, ...baseTrain }));
  const trains = Array.isArray(safeRoute.trains) && safeRoute.trains.length
    ? safeRoute.trains.map((train) => normalizeTrain(train, baseTrain))
    : [baseTrain];

  return {
    ...safeRoute,
    ...baseTrain,
    id: safeRoute.id || `${safeRoute.source || "SRC"}-${safeRoute.destination || "DST"}-${baseTrain.train_no}-${index}`,
    train: baseTrain,
    primary_train: baseTrain,
    primary_train_no: baseTrain.train_no,
    primary_train_name: baseTrain.train_name,
    trains,
    legs,
    segments: Array.isArray(safeRoute.segments) && safeRoute.segments.length ? safeRoute.segments.map((segment) => normalizeLeg(segment, { ...safeRoute, ...baseTrain })) : legs,
    title: safeRoute.title || `${baseTrain.train_no} ${baseTrain.train_name}`,
    display_title: safeRoute.display_title || `${baseTrain.train_no} ${baseTrain.train_name}`,
    label: safeRoute.label || `${baseTrain.train_no} ${baseTrain.train_name}`,
    route_type: safeRoute.route_type || safeRoute.type || "direct",
    type: safeRoute.type || safeRoute.route_type || "direct",
    transfer_count: Number(safeRoute.transfer_count || safeRoute.transfers || 0),
    transfers: Number(safeRoute.transfers || safeRoute.transfer_count || 0),
    duration: safeRoute.duration || safeRoute.duration_label || legs[0]?.duration || "14h 25m",
    duration_label: safeRoute.duration_label || safeRoute.duration || legs[0]?.duration_label || "14h 25m",
    duration_minutes: Number(safeRoute.duration_minutes || safeRoute.total_duration_minutes || legs[0]?.duration_minutes || 865),
    total_duration_minutes: Number(safeRoute.total_duration_minutes || safeRoute.duration_minutes || legs[0]?.duration_minutes || 865),
    score: Number(safeRoute.score || safeRoute.rank_score || 934),
    rank_score: Number(safeRoute.rank_score || safeRoute.score || 934),
  };
}

export function normalizeSearchPayload(payload) {
  const safePayload = payload && typeof payload === "object" ? payload : {};
  const rawRoutes = safePayload.routes || safePayload.recommendations || safePayload.direct_routes || safePayload.smart_routes || [];
  const routes = Array.isArray(rawRoutes) ? rawRoutes.map(normalizeRoute) : [];
  const best = routes[0] || null;
  return {
    ...safePayload,
    ok: safePayload.ok !== false,
    status: safePayload.status || "ok",
    route_exists: routes.length > 0,
    count: routes.length,
    total_routes: routes.length,
    total_options: routes.length,
    direct_count: Number(safePayload.direct_count || routes.length),
    one_transfer_count: Number(safePayload.one_transfer_count || 0),
    smart_count: Number(safePayload.smart_count || routes.length),
    routes,
    recommendations: routes,
    direct_routes: safePayload.direct_routes ? safePayload.direct_routes.map(normalizeRoute) : routes,
    smart_routes: safePayload.smart_routes ? safePayload.smart_routes.map(normalizeRoute) : routes,
    transfer_routes: safePayload.transfer_routes ? safePayload.transfer_routes.map(normalizeRoute) : [],
    best_direct: normalizeRoute(safePayload.best_direct || best),
    best_smart: normalizeRoute(safePayload.best_smart || best),
    best_transfer: safePayload.best_transfer ? normalizeRoute(safePayload.best_transfer) : best ? normalizeRoute(best) : null,
    best_available: normalizeRoute(safePayload.best_available || safePayload.summary?.best_available || best),
    summary: {
      ...(safePayload.summary || {}),
      best_available: normalizeRoute(safePayload.summary?.best_available || safePayload.best_available || best),
      best_direct: normalizeRoute(safePayload.summary?.best_direct || safePayload.best_direct || best),
      best_smart: normalizeRoute(safePayload.summary?.best_smart || safePayload.best_smart || best),
      best_transfer: safePayload.summary?.best_transfer ? normalizeRoute(safePayload.summary.best_transfer) : best ? normalizeRoute(best) : null,
    },
  };
}
