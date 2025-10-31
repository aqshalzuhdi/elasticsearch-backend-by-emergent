import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database, Package, FileText, Search, Activity } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const navigate = useNavigate();
  const [esHealth, setEsHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkElasticsearchHealth();
  }, []);

  const checkElasticsearchHealth = async () => {
    try {
      const response = await axios.get(`${API}/elasticsearch/health`);
      setEsHealth(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Elasticsearch health check failed:', error);
      setEsHealth({ status: 'disconnected' });
      setLoading(false);
    }
  };

  const createIndices = async () => {
    try {
      const response = await axios.post(`${API}/elasticsearch/indices/create`);
      toast.success('Indices created successfully!');
      console.log(response.data);
    } catch (error) {
      toast.error('Failed to create indices');
      console.error(error);
    }
  };

  const navCards = [
    {
      title: 'Production Orders',
      description: 'Manage production orders and view details',
      icon: Package,
      path: '/production-orders',
      color: 'from-blue-500 to-blue-600'
    },
    {
      title: 'Traceabilities',
      description: 'Track and manage traceability records',
      icon: Activity,
      path: '/traceabilities',
      color: 'from-green-500 to-green-600'
    },
    {
      title: 'Nameplates',
      description: 'View and manage nameplate information',
      icon: FileText,
      path: '/nameplates',
      color: 'from-purple-500 to-purple-600'
    },
    {
      title: 'Search',
      description: 'Advanced search across all indices',
      icon: Search,
      path: '/search',
      color: 'from-orange-500 to-orange-600'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-6 shadow-lg">
            <Database className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-5xl font-bold text-slate-800 mb-4">
            Elasticsearch Data Manager
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Manage your production orders, traceabilities, and nameplates with powerful search capabilities
          </p>
        </div>

        <Card className="mb-8 border-2 shadow-lg" data-testid="health-status-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`w-3 h-3 rounded-full ${
                    esHealth?.status === 'connected' ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                  }`}
                />
                <span className="text-lg font-medium">
                  Elasticsearch: {loading ? 'Checking...' : esHealth?.status === 'connected' ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex gap-3">
                <Button onClick={checkElasticsearchHealth} variant="outline" data-testid="refresh-health-btn">
                  Refresh Status
                </Button>
                <Button onClick={createIndices} data-testid="create-indices-btn">
                  Initialize Indices
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {navCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <Card
                key={index}
                className="cursor-pointer transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 border-2 overflow-hidden group"
                onClick={() => navigate(card.path)}
                data-testid={`nav-card-${card.path.replace('/', '')}`}
              >
                <div className={`h-2 bg-gradient-to-r ${card.color}`} />
                <CardHeader>
                  <div className={`inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br ${card.color} rounded-xl mb-4 group-hover:scale-110 transition-transform`}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <CardTitle className="text-xl">{card.title}</CardTitle>
                  <CardDescription className="text-base">{card.description}</CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>

        <div className="mt-12 text-center">
          <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-2">
            <CardContent className="pt-6">
              <h3 className="text-xl font-semibold text-slate-800 mb-2">Quick Actions</h3>
              <p className="text-slate-600 mb-4">
                Initialize your Elasticsearch indices or explore existing data using the navigation cards above
              </p>
              <div className="flex gap-3 justify-center">
                <Button variant="outline" onClick={() => navigate('/search')} data-testid="quick-search-btn">
                  <Search className="w-4 h-4 mr-2" />
                  Quick Search
                </Button>
                <Button onClick={() => navigate('/production-orders')} data-testid="quick-production-orders-btn">
                  <Package className="w-4 h-4 mr-2" />
                  View Production Orders
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
