import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  MapContainer,
  TileLayer,
  Polyline,
  Marker,
  Popup,
  useMap,
  LayersControl,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Icons
const incidentIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/684/684908.png',
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [0, -30],
});
const getSeverityClass = (severity: string = '') => {
  switch (severity) {
    case 'High':
      return 'bg-red-100 text-red-800';
    case 'Medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'Low':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
  shadowSize: [41, 41],
});

const destinationIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/535/535137.png',
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [0, -30],
});

export default function MapPage() {
  const [incidents, setIncidents] = useState([]);
  const [userLocation, setUserLocation] = useState<{lat: number; lng: number } | null>(null);
  const [destination, setDestination] = useState('');
  const [destinationCoord, setDestinationCoord] = useState<{ lat: number; lng: number } | null>(null);

  type RouteInfo = {
    distance: number;
    duration: number;
    route: [number, number][];
  };
  
  const [routeInfo, setRouteInfo] = useState<RouteInfo | null>(null);
  const [routeIncidents, setRouteIncidents] = useState<any[]>([]);
  
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios
      .get(`${import.meta.env.VITE_BACKEND_URL}/api/incidents`)
      .then((res) => setIncidents(res.data))
      .catch(console.error);
  }, []);

  useEffect(() => {
    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setError(null); // Clear error when position is successfully fetched
      },
      (err) => {
        setError('Geolocation error: ' + err.message); // Set the error message here
      },
      {
        enableHighAccuracy: true,
        maximumAge: 5000,
        timeout: 10000,
      }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  const getCurrentLocation = () => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setError(null); // Clear error when position is successfully fetched
      },
      (err) => {
        setError('Geolocation error: ' + err.message); // Set the error message here
      }
    );
  };

  const geocodeDestination = async (place: string): Promise<{ lat: number; lng: number }> => {
    if (!place || place.trim() === '') {
      throw new Error('Invalid destination');
    }
  
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(place)}&format=json&limit=1`;
    const { data } = await axios.get(url);
    if (data.length === 0) throw new Error('Destination not found');
  
    const { lat, lon } = data[0];
    return { lat: Number(lat), lng: Number(lon) };
  };
  

  const findRoute = async () => {
    if (!userLocation || !destination) {
      setError('Please provide a valid location and destination.');
      return;
    }

    try {
      setLoading(true);
      const destCoord = await geocodeDestination(destination);
      setDestinationCoord(destCoord);

      const { data } = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/api/route-info`, {
        params: {
          origin: `${userLocation.lng},${userLocation.lat}`,
          destination: `${destCoord.lng},${destCoord.lat}`,
        },
      });

      setRouteInfo({
        distance: data.distance_km,
        duration: data.duration_min,
        route: data.route.map,
      });
      setRouteIncidents(data.incidents);

      await axios.post(`${import.meta.env.VITE_BACKEND_URL}/api/reports`, {
        origin: `${userLocation.lng},${userLocation.lat}`,
        destination: `${destCoord.lng},${destCoord.lat}`,
        distance_km: data.distance_km,
        duration_min: data.duration_min,
        incidents: data.incidents,
      });

      setError(null);
    } catch (e) {
      setError('An error occurred while finding the route: ' + (e instanceof Error ? e.message : String(e)));
    }finally{
      setLoading(false);
    }
  };

  const MapUpdater = ({ position }: { position: { lat: number; lng: number } | null }) => {
    const map = useMap();
  
    useEffect(() => {
      if (position) {
        // Only update the map view if position is defined
        map.setView([position.lat, position.lng], 14);
      }
    }, [position, map]);
  
    return null;
  };
  
  return (
    <div className="relative h-screen w-screen">
      {/* Controls */}
      <div className="absolute top-5 left-1/2 transform -translate-x-1/2 z-[1000] bg-white/90 backdrop-blur-md shadow-lg rounded-xl px-6 py-4 w-full max-w-xl">
        <div className="flex flex-col sm:flex-row items-center gap-2">
          <button onClick={getCurrentLocation} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded w-full sm:w-auto">
            Use My Location
          </button>
          <input
            type="text"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Destination (e.g., Empire State Building)"
            className="flex-1 px-4 py-2 rounded border w-full"
          />
          <button onClick={findRoute} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded w-full sm:w-auto">
            Find Route
          </button>
        </div>
        {loading && <p className="text-blue-600 mt-2">🛰 Calculating route...</p>}
        {error && <p className="text-red-600 mt-2">{error}</p>}
        {routeInfo && (
          <div className="mt-2 text-sm text-gray-800">
            <strong>Distance:</strong> {routeInfo.distance} km · <strong>ETA:</strong> {routeInfo.duration} min
          </div>
        )}
      </div>

      {/* Map */}
      <MapContainer center={userLocation ? [userLocation.lat, userLocation.lng] : [40.7128, -74.006]} zoom={13} scrollWheelZoom className="h-full w-full z-0">
        <MapUpdater position={userLocation} />
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="Street (OSM)">
            <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite (Esri)">
            <TileLayer attribution="Tiles &copy; Esri" url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" />
          </LayersControl.BaseLayer>
        </LayersControl>

        {userLocation && <Marker position={userLocation} icon={defaultIcon}><Popup>You are here</Popup></Marker>}
        {destinationCoord && <Marker position={destinationCoord} icon={destinationIcon}><Popup>Destination</Popup></Marker>}

        {routeInfo?.route && <Polyline positions={routeInfo.route} pathOptions={{ color: '#4285F4', weight: 6 }} />}

        {routeIncidents.map((inc, idx) => (
          <Marker key={`route-${idx}`} position={[inc.lat, inc.lng]} icon={incidentIcon}>
            <Popup>
              <div className="text-sm">
                <strong>{inc.type}</strong><br />
                Severity: <span className="font-semibold">{inc.severity}</span>
              </div>
            </Popup>
          </Marker>
        ))}


</MapContainer>

      {/* Incident Lists */}
      <div className="absolute bottom-4 right-4 z-[1000] w-[300px] max-h-[300px] overflow-y-auto bg-white/90 backdrop-blur-md shadow-lg rounded-xl p-4">
        {routeIncidents.length > 0 && (
          <>
            <h3 className="text-lg font-semibold mb-2">Route Incidents</h3>
            {routeIncidents.map((inc, idx) => (
              <div key={`route-${idx}`} className="mb-2">
                <div className={`px-3 py-2 rounded-lg text-sm font-medium shadow-sm ${
                  inc.severity === 'High' ? 'bg-red-100 text-red-800'
                  : inc.severity === 'Medium' ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-green-100 text-green-800'
                }`}>
                  {inc.type} @ {inc.location} ({inc.severity})
                </div>
              </div>
            ))}
            <hr className="my-2" />
          </>
        )}
        <h3 className="text-lg font-semibold mb-2">All Incidents</h3>
        {incidents.map((inc, idx) => (
          <div key={`all-${idx}`} className="mb-2">
            <div className={`px-3 py-2 rounded-lg text-sm font-medium shadow-sm ${
              inc.severity === 'High' ? 'bg-red-100 text-red-800'
              : inc.severity === 'Medium' ? 'bg-yellow-100 text-yellow-800'
              : 'bg-green-100 text-green-800'
            }`}>
              {inc.type} @ {inc.location} ({inc.severity})
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
