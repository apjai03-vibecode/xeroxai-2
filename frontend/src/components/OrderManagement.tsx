"use client";

import React, { useState, useEffect } from "react";
import {
  ShoppingBag,
  Search,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertCircle,
  Phone,
  User,
  Calendar,
  Layers,
  ArrowRight,
  Filter
} from "lucide-react";
import { Order } from "../lib/types";
import { getOrdersApi, updateOrderStatusApi } from "../lib/api";

export function OrderManagement({ refreshSignal }: { refreshSignal?: number }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchOrders = async () => {
    setIsLoading(true);
    try {
      const data = await getOrdersApi(statusFilter, searchQuery);
      setOrders(data);
    } catch (err) {
      console.error("Failed to load orders:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [statusFilter, refreshSignal]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchOrders();
  };

  const handleStatusChange = async (
    orderId: string,
    newStatus: "Pending" | "Processing" | "Completed"
  ) => {
    setUpdatingId(orderId);
    try {
      await updateOrderStatusApi(orderId, newStatus);
      fetchOrders();
    } catch (err: any) {
      alert("Failed to update status: " + err.message);
    } finally {
      setUpdatingId(null);
    }
  };

  // Metrics summary
  const totalOrders = orders.length;
  const pendingCount = orders.filter((o) => o.status === "Pending").length;
  const processingCount = orders.filter((o) => o.status === "Processing").length;
  const completedCount = orders.filter((o) => o.status === "Completed").length;
  const totalRevenue = orders.reduce((sum, o) => sum + o.total_amount, 0);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-amber-50 text-amber-600 border border-amber-100 shadow-2xs">
            <ShoppingBag className="h-6 w-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                Order Management System
              </h2>
              <span className="px-2.5 py-1 text-xs font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200 rounded-lg">
                Persistent SQLite
              </span>
            </div>
            <p className="text-sm text-slate-500 font-medium mt-0.5">
              Track customer orders, itemized print jobs, billing totals, and lifecycle statuses.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={fetchOrders}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-sm font-semibold transition-colors self-start sm:self-auto shadow-2xs"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin text-indigo-600" : ""}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Metrics Summary Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <span className="text-xs text-slate-500 uppercase font-mono font-bold block">Total Orders</span>
          <span className="text-2xl font-black text-slate-900 font-mono mt-1 block">{totalOrders}</span>
        </div>
        <div className="bg-amber-50/70 p-4 rounded-xl border border-amber-200">
          <span className="text-xs text-amber-700 uppercase font-mono font-bold block">Pending</span>
          <span className="text-2xl font-black text-amber-800 font-mono mt-1 block">{pendingCount}</span>
        </div>
        <div className="bg-blue-50/70 p-4 rounded-xl border border-blue-200">
          <span className="text-xs text-blue-700 uppercase font-mono font-bold block">Processing</span>
          <span className="text-2xl font-black text-blue-800 font-mono mt-1 block">{processingCount}</span>
        </div>
        <div className="bg-emerald-50/70 p-4 rounded-xl border border-emerald-200">
          <span className="text-xs text-emerald-700 uppercase font-mono font-bold block">Completed</span>
          <span className="text-2xl font-black text-emerald-800 font-mono mt-1 block">{completedCount}</span>
        </div>
        <div className="col-span-2 sm:col-span-1 bg-indigo-50/70 p-4 rounded-xl border border-indigo-200">
          <span className="text-xs text-indigo-700 uppercase font-mono font-bold block">Queue Value</span>
          <span className="text-2xl font-black text-indigo-900 font-mono mt-1 block">₹{totalRevenue.toFixed(0)}</span>
        </div>
      </div>

      {/* Filters & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-50 p-3 rounded-2xl border border-slate-200 text-sm">
        {/* Status Pill Tabs */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {["All", "Pending", "Processing", "Completed"].map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`px-3.5 py-1.5 rounded-xl font-bold text-xs transition-all ${
                statusFilter === st
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Search input */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-72">
            <Search className="h-4 w-4 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by customer, phone, or ID..."
              className="w-full bg-white border border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 rounded-xl pl-9 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 outline-none transition-all shadow-2xs font-medium"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition-colors shadow-2xs"
          >
            Find
          </button>
        </form>
      </div>

      {/* Orders List / Cards */}
      <div className="flex flex-col gap-3.5">
        {orders.length === 0 ? (
          <div className="p-10 text-center bg-slate-50 rounded-2xl border border-slate-200 text-slate-500 text-sm font-medium">
            No orders found matching the selected filter. Create one using the Smart Billing engine above!
          </div>
        ) : (
          orders.map((order) => (
            <div
              key={order.order_id}
              className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-5 transition-all shadow-2xs hover:shadow-xs"
            >
              {/* Order Identity & Customer */}
              <div className="flex flex-col gap-1.5 max-w-sm">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono font-bold text-xs text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-200">
                    {order.order_id}
                  </span>
                  <span
                    className={`text-xs font-mono px-2.5 py-0.5 rounded-full font-bold uppercase ${
                      order.status === "Pending"
                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                        : order.status === "Processing"
                        ? "bg-blue-100 text-blue-800 border border-blue-300"
                        : "bg-emerald-100 text-emerald-800 border border-emerald-300"
                    }`}
                  >
                    {order.status}
                  </span>
                </div>

                <div className="flex items-center gap-3 text-sm text-slate-900 font-bold mt-1">
                  <span className="flex items-center gap-1.5">
                    <User className="h-4 w-4 text-slate-500" />
                    <span>{order.customer_name}</span>
                  </span>
                  {order.customer_phone && (
                    <span className="flex items-center gap-1 text-slate-500 font-mono text-xs font-medium">
                      <Phone className="h-3.5 w-3.5" />
                      <span>{order.customer_phone}</span>
                    </span>
                  )}
                </div>

                {order.notes && (
                  <p className="text-xs text-slate-500 italic">
                    Note: {order.notes}
                  </p>
                )}
              </div>

              {/* Items Breakdown */}
              <div className="flex-1 text-xs text-slate-700">
                <div className="font-bold text-slate-500 text-xs uppercase font-mono mb-1.5">
                  Job Items ({order.items.length})
                </div>
                <div className="flex flex-col gap-1.5">
                  {order.items.map((item, idx) => (
                    <div key={idx} className="text-slate-800 text-xs flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
                      <span className="font-medium">{item.description || `${item.page_count} pages ${item.paper_size}`}</span>
                      <span className="text-slate-500 font-mono">
                        (₹{item.subtotal?.toFixed(2) || "0.00"})
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Total & Action Buttons */}
              <div className="flex flex-col sm:flex-row md:flex-col lg:flex-row items-end md:items-center gap-4 w-full md:w-auto pt-3 md:pt-0 border-t md:border-t-0 border-slate-200">
                <div className="text-right">
                  <span className="text-xs text-slate-400 block uppercase font-mono font-bold">Total Bill</span>
                  <span className="text-2xl font-black font-mono text-emerald-600">
                    ₹{order.total_amount.toFixed(2)}
                  </span>
                </div>

                {/* Status Switcher */}
                <div className="flex items-center gap-2">
                  {order.status === "Pending" && (
                    <button
                      type="button"
                      disabled={updatingId === order.order_id}
                      onClick={() => handleStatusChange(order.order_id, "Processing")}
                      className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-bold transition-all shadow-xs"
                    >
                      Start Processing
                    </button>
                  )}
                  {order.status === "Processing" && (
                    <button
                      type="button"
                      disabled={updatingId === order.order_id}
                      onClick={() => handleStatusChange(order.order_id, "Completed")}
                      className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-xs font-bold transition-all shadow-xs"
                    >
                      Mark Completed
                    </button>
                  )}
                  {order.status === "Completed" && (
                    <span className="text-xs text-emerald-700 font-mono font-bold flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Ready for pickup
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
