import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Package, RefreshCw, Eye } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProductionOrders = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showDialog, setShowDialog] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/elasticsearch/production-orders?size=100`);
      setOrders(response.data.data || []);
      toast.success(`Loaded ${response.data.total} production orders`);
    } catch (error) {
      console.error('Failed to fetch production orders:', error);
      toast.error('Failed to load production orders');
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const viewDetails = (order) => {
    setSelectedOrder(order);
    setShowDialog(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/')} data-testid="back-to-dashboard-btn">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-4xl font-bold text-slate-800 flex items-center gap-3">
                <Package className="w-10 h-10" />
                Production Orders
              </h1>
              <p className="text-slate-600 mt-1">Manage and view all production orders</p>
            </div>
          </div>
          <Button onClick={fetchOrders} disabled={loading} data-testid="refresh-orders-btn">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        ) : orders.length === 0 ? (
          <Card className="border-2">
            <CardContent className="py-12 text-center">
              <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-700 mb-2">No Production Orders Found</h3>
              <p className="text-slate-500 mb-4">Initialize indices and add some data to get started</p>
              <Button onClick={() => navigate('/')} data-testid="go-home-btn">
                Go to Dashboard
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {orders.map((order, index) => (
              <Card
                key={order.id || index}
                className="border-2 hover:shadow-xl transition-all duration-300 cursor-pointer"
                onClick={() => viewDetails(order)}
                data-testid={`order-card-${order.id}`}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-xl mb-2">{order.identity_number}</CardTitle>
                      <CardDescription className="text-base">{order.product_code}</CardDescription>
                    </div>
                    <Badge variant="outline" className="text-sm">
                      ID: {order.id}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Quantity:</span>
                      <span className="font-semibold text-slate-800">{order.qty} PCE</span>
                    </div>
                    {order.customer && (
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">Customer:</span>
                        <span className="font-semibold text-slate-800">{order.customer.customer}</span>
                      </div>
                    )}
                    {order.status && (
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">Status:</span>
                        <Badge style={{ backgroundColor: order.status.bg_color }}>
                          {order.status.status}
                        </Badge>
                      </div>
                    )}
                    {order.planning_date && (
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">Planning Date:</span>
                        <span className="font-semibold text-slate-800">{order.planning_date}</span>
                      </div>
                    )}
                  </div>
                  <Button className="w-full mt-4" variant="outline" data-testid={`view-details-btn-${order.id}`}>
                    <Eye className="w-4 h-4 mr-2" />
                    View Details
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto" data-testid="order-details-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl">Production Order Details</DialogTitle>
          </DialogHeader>
          {selectedOrder && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-lg">
                <h3 className="font-semibold text-lg mb-3">Basic Information</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-600">ID:</span>
                    <span className="ml-2 font-semibold">{selectedOrder.id}</span>
                  </div>
                  <div>
                    <span className="text-slate-600">Identity Number:</span>
                    <span className="ml-2 font-semibold">{selectedOrder.identity_number}</span>
                  </div>
                  <div>
                    <span className="text-slate-600">Product Code:</span>
                    <span className="ml-2 font-semibold">{selectedOrder.product_code}</span>
                  </div>
                  <div>
                    <span className="text-slate-600">Quantity:</span>
                    <span className="ml-2 font-semibold">{selectedOrder.qty} PCE</span>
                  </div>
                </div>
              </div>

              {selectedOrder.customer && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-lg mb-3">Customer Information</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-slate-600">Name:</span>
                      <span className="ml-2 font-semibold">{selectedOrder.customer.customer}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Description:</span>
                      <span className="ml-2 font-semibold">{selectedOrder.customer.description}</span>
                    </div>
                  </div>
                </div>
              )}

              {selectedOrder.traceabilities && selectedOrder.traceabilities.length > 0 && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-lg mb-3">Traceabilities ({selectedOrder.traceabilities.length})</h3>
                  <div className="space-y-2">
                    {selectedOrder.traceabilities.map((trace, idx) => (
                      <div key={idx} className="bg-white p-3 rounded border">
                        <div className="text-sm">
                          <span className="text-slate-600">Station ID:</span>
                          <span className="ml-2 font-semibold">{trace.station_id}</span>
                          {trace.station && (
                            <span className="ml-2 text-slate-600">({trace.station.station})</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-xs">
                {JSON.stringify(selectedOrder, null, 2)}
              </pre>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProductionOrders;
