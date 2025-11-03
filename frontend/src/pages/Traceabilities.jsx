import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Activity, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import moment from "moment";
import "moment/locale/id";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Traceabilities = () => {
  const navigate = useNavigate();
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTraces();
  }, []);

  const fetchTraces = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/elasticsearch/traceabilities?size=100`);
      setTraces(response.data.data || []);
      toast.success(`Loaded ${response.data.total} traceabilities`);
    } catch (error) {
      console.error('Failed to fetch traceabilities:', error);
      toast.error('Failed to load traceabilities');
      setTraces([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-green-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/')} data-testid="back-to-dashboard-btn">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-4xl font-bold text-slate-800 flex items-center gap-3">
                <Activity className="w-10 h-10" />
                Traceabilities
              </h1>
              <p className="text-slate-600 mt-1">Track and manage traceability records</p>
            </div>
          </div>
          <Button onClick={fetchTraces} disabled={loading} data-testid="refresh-traces-btn">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600" />
          </div>
        ) : traces.length === 0 ? (
          <Card className="border-2">
            <CardContent className="py-12 text-center">
              <Activity className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-700 mb-2">No Traceabilities Found</h3>
              <p className="text-slate-500 mb-4">Add some traceability data to get started</p>
              <Button onClick={() => navigate('/')} data-testid="go-home-btn">
                Go to Dashboard
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {traces.map((trace, index) => {
                let created_at = moment(trace.created_at).locale('id').format("DD MMM YYYY HH:mm:ss");

                return (
                  <Card
                    key={trace.id || index}
                    className="border-2 hover:shadow-xl transition-all duration-300"
                    data-testid={`trace-card-${trace.id}`}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-xl mb-2">Trace #{trace.id}</CardTitle>
                          <CardDescription className="text-base">
                            {/* {trace.model_type?.split('\\').pop()} */}
                            {created_at}
                          </CardDescription>
                        </div>
                        <Badge variant="outline" className="text-sm">
                          Model: {trace.model_id}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600">Station ID:</span>
                          <span className="font-semibold text-slate-800">{trace.station_id}</span>
                        </div>
                        {trace.station && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Station:</span>
                            <span className="font-semibold text-slate-800">{trace.station.station}</span>
                          </div>
                        )}
                        {trace.status && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Status:</span>
                            <Badge style={{ backgroundColor: trace.status.bg_color }}>
                              {trace.status.status}
                            </Badge>
                          </div>
                        )}
                        {trace.user_id && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">User ID:</span>
                            <span className="font-semibold text-slate-800">{trace.user_id}</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )
              }
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Traceabilities;
