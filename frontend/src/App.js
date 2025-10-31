import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import Dashboard from "@/pages/Dashboard";
import ProductionOrders from "@/pages/ProductionOrders";
import Traceabilities from "@/pages/Traceabilities";
import Nameplates from "@/pages/Nameplates";
import Search from "@/pages/Search";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/production-orders" element={<ProductionOrders />} />
          <Route path="/traceabilities" element={<Traceabilities />} />
          <Route path="/nameplates" element={<Nameplates />} />
          <Route path="/search" element={<Search />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;
