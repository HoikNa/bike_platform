// ── Enum 타입 ─────────────────────────────────────────────────
export type VehicleStatus = "RUNNING" | "IDLE" | "CHARGING" | "ALERT" | "OFFLINE"
export type AlertSeverity = "INFO" | "WARNING" | "DANGER"
export type AlertType =
  | "OVERSPEED"
  | "BATTERY_LOW"
  | "BATTERY_CRITICAL"
  | "GEOFENCE_EXIT"
  | "SUDDEN_ACCEL"
  | "SUDDEN_BRAKE"
  | "ACCIDENT_SUSPECTED"
  | "MAINTENANCE_DUE"
  | "COMMUNICATION_LOST"
export type UserRole = "ADMIN" | "MANAGER" | "DRIVER"

// ── 사용자 ────────────────────────────────────────────────────
export interface User {
  id:        string
  email:     string
  full_name: string
  role:      UserRole
  is_active: boolean
}

// ── 운전자 프로필 ─────────────────────────────────────────────
export interface DriverProfile {
  id:                string
  user_full_name:    string
  license_number:    string
  license_expiry:    string
  phone:             string
  emergency_contact: string | null
}

// ── 최신 센서 데이터 스냅샷 ───────────────────────────────────
export interface LatestSensor {
  time:                string
  latitude:            number | null
  longitude:           number | null
  speed_kmh:           number | null
  battery_level_pct:   number | null
  battery_voltage_v:   number | null
  battery_temp_celsius: number | null
  engine_rpm:          number | null
  odometer_km:         number | null
}

// ── 차량 ──────────────────────────────────────────────────────
export interface Vehicle {
  id:                    string
  plate_number:          string
  model:                 string
  manufacturer:          string
  manufacture_year:      number
  status:                VehicleStatus
  battery_capacity_kwh:  number
  vin:                   string | null
  assigned_driver:       DriverProfile | null
  latest_sensor:         LatestSensor | null
  active_trip:           ActiveTrip | null
  unacknowledged_alerts_count: number
  created_at:            string
  updated_at:            string
}

export interface ActiveTrip {
  id:            string
  started_at:    string
  start_address: string | null
}

// ── 알림 ──────────────────────────────────────────────────────
export interface Alert {
  id:                  string
  vehicle:             { id: string; plate_number: string }
  triggered_at:        string
  alert_type:          AlertType
  severity:            AlertSeverity
  title:               string
  description:         string | null
  speed_at_trigger:    number | null
  battery_at_trigger:  number | null
  location_lat:        number | null
  location_lng:        number | null
  is_acknowledged:     boolean
  acknowledged_by:     { id: string; full_name: string } | null
  acknowledged_at:     string | null
  created_at:          string
}

// ── 운행 기록 ─────────────────────────────────────────────────
export interface Trip {
  id:                string
  vehicle:           { id: string; plate_number: string }
  driver:            { id: string; user_full_name: string } | null
  started_at:        string
  ended_at:          string | null
  start_address:     string | null
  end_address:       string | null
  distance_km:       number | null
  avg_speed_kmh:     number | null
  max_speed_kmh:     number | null
  battery_start_pct: number | null
  battery_end_pct:   number | null
  alert_count:       number
}

// ── 충전소 ────────────────────────────────────────────────────
export interface ChargingStation {
  id:               string
  name:             string
  address:          string
  latitude:         number
  longitude:        number
  distance_km?:     number
  total_slots:      number
  available_slots:  number
  operator_name:    string | null
  contact_phone:    string | null
  is_active:        boolean
}

// ── WebSocket 이벤트 페이로드 ─────────────────────────────────
export interface WsLocationPayload {
  vehicle_id:        string
  timestamp:         string
  latitude:          number
  longitude:         number
  heading_deg:       number | null
  speed_kmh:         number
  battery_level_pct: number
  status:            VehicleStatus
}

export interface WsBatteryPayload {
  vehicle_id:             string
  plate_number:           string
  driver_id:              string
  current_battery_pct:    number
  estimated_depletion_min: number
  recommended_action:     string
  nearest_stations:       Pick<ChargingStation, "id" | "name" | "distance_km" | "available_slots">[]
  triggered_at:           string
}
