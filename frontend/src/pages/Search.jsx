import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Search as SearchIcon } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Search = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [index, setIndex] = useState('production_orders_v1');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setLoading(true);
    setSearched(true);
    try {
      const response = await axios.post(`${API}/elasticsearch/search`, {
        query,
        index,
        size: 50
      });
      setResults(response.data.data || []);
      toast.success(`Found ${response.data.total} results`);
    } catch (error) {
      console.error('Search failed:', error);
      toast.error('Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-orange-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center gap-4 mb-8">
          <Button variant="outline" onClick={() => navigate('/')} data-testid="back-to-dashboard-btn">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-4xl font-bold text-slate-800 flex items-center gap-3">
              <SearchIcon className="w-10 h-10" />
              Advanced Search
            </h1>
            <p className="text-slate-600 mt-1">Search across all Elasticsearch indices</p>
          </div>
        </div>

        <Card className="mb-8 border-2 shadow-lg">
          <CardHeader>
            <CardTitle>Search Parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label htmlFor="search-query" className="text-base mb-2 block">
                  Search Query
                </Label>
                <Input
                  id="search-query"
                  placeholder="Enter search terms (e.g., AJI, 2251030001, WH_JIG_REPORT)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="text-base"
                  data-testid="search-query-input"
                />
              </div>
              <div>
                <Label htmlFor="search-index" className="text-base mb-2 block">
                  Index
                </Label>
                <Select value={index} onValueChange={setIndex}>
                  <SelectTrigger data-testid="index-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="production_orders_v1">Production Orders</SelectItem>
                    <SelectItem value="traceabilities_v1">Traceabilities</SelectItem>
                    <SelectItem value="nameplates_v1">Nameplates</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={handleSearch}
                disabled={loading}
                className="w-full"
                size="lg"
                data-testid="search-btn"
              >
                <SearchIcon className={`w-5 h-5 mr-2 ${loading ? 'animate-pulse' : ''}`} />
                {loading ? 'Searching...' : 'Search'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {searched && (
          <Card className="border-2">
            <CardHeader>
              <CardTitle>
                Search Results ({results.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {results.length === 0 ? (
                <div className="text-center py-8">
                  <SearchIcon className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-600">No results found for "{query}"</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {results.map((result, idx) => (
                    <Card key={idx} className="border" data-testid={`search-result-${idx}`}>
                      <CardContent className="pt-4">
                        <pre className="bg-slate-50 p-4 rounded overflow-x-auto text-xs">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Search;
