import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, FileText, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import moment from "moment";
import "moment/locale/id";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Nameplates = () => {
  const navigate = useNavigate();
  const [nameplates, setNameplates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNameplates();
  }, []);

  const fetchNameplates = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/elasticsearch/nameplates?size=100`);
      setNameplates(response.data.data || []);
      toast.success(`Loaded ${response.data.total} nameplates`);
    } catch (error) {
      console.error('Failed to fetch nameplates:', error);
      toast.error('Failed to load nameplates');
      setNameplates([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/')} data-testid="back-to-dashboard-btn">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-4xl font-bold text-slate-800 flex items-center gap-3">
                <FileText className="w-10 h-10" />
                Nameplates
              </h1>
              <p className="text-slate-600 mt-1">View and manage nameplate information</p>
            </div>
          </div>
          <Button onClick={fetchNameplates} disabled={loading} data-testid="refresh-nameplates-btn">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600" />
          </div>
        ) : nameplates.length === 0 ? (
          <Card className="border-2">
            <CardContent className="py-12 text-center">
              <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-700 mb-2">No Nameplates Found</h3>
              <p className="text-slate-500 mb-4">Add some nameplate data to get started</p>
              <Button onClick={() => navigate('/')} data-testid="go-home-btn">
                Go to Dashboard
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {nameplates.map((nameplate, index) => {
                let created_at = moment(nameplate.created_at).locale('id').format("DD MMM YYYY HH:mm:ss");

                return (
                  <Card
                    key={nameplate.id || index}
                    className="border-2 hover:shadow-xl transition-all duration-300"
                    data-testid={`nameplate-card-${nameplate.id}`}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-xl mb-2">{nameplate.identity_number}</CardTitle>
                          <CardDescription className="text-base">Flag: {nameplate.flag}</CardDescription>
                        </div>
                        <Badge variant="outline" className="text-sm">
                          ID: {nameplate.id}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600">Created:</span>
                          <span className="font-semibold text-slate-800">{created_at}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600">Production Order:</span>
                          <span className="font-semibold text-slate-800">{nameplate.production_order_id}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600">Station ID:</span>
                          <span className="font-semibold text-slate-800">{nameplate.station_id}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600">User ID:</span>
                          <span className="font-semibold text-slate-800">{nameplate.user_id}</span>
                        </div>
                        {nameplate.shift_id && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Shift ID:</span>
                            <span className="font-semibold text-slate-800">{nameplate.shift_id}</span>
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

export default Nameplates;
