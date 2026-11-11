import { createBrowserRouter } from "react-router"

import { AppShell } from "@/app/AppShell"
import { NotFoundPage } from "@/app/PlaceholderPage"
import { BulkRunDetailPage, BulkRunsPage } from "@/features/bulk/BulkRunsPage"
import { ComparePage } from "@/features/compare/ComparePage"
import { ComparisonDetailPage } from "@/features/comparisons/ComparisonDetailPage"
import { ComparisonsPage } from "@/features/comparisons/ComparisonsPage"
import { DashboardPage } from "@/features/dashboard/DashboardPage"
import { ExecutionDetailPage } from "@/features/executions/ExecutionDetailPage"
import { ExecutionsPage } from "@/features/executions/ExecutionsPage"
import { SettingsPage } from "@/features/settings/SettingsPage"
import { NewTicketPage } from "@/features/tickets/NewTicketPage"
import { TicketDetailPage } from "@/features/tickets/TicketDetailPage"
import { TicketListPage } from "@/features/tickets/TicketListPage"

// Routes from design.md section 3. `handle.title` names the page in the header and browser tab.
export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      {
        index: true,
        handle: { title: "Overview" },
        element: <DashboardPage />,
      },
      {
        path: "tickets",
        handle: { title: "Tickets" },
        element: <TicketListPage />,
      },
      {
        path: "tickets/new",
        handle: { title: "New Ticket" },
        element: <NewTicketPage />,
      },
      {
        path: "tickets/:ticketId",
        handle: { title: "Ticket" },
        element: <TicketDetailPage />,
      },
      {
        path: "compare",
        handle: { title: "Compare" },
        element: <ComparePage />,
      },
      {
        path: "comparisons",
        handle: { title: "Comparisons" },
        element: <ComparisonsPage />,
      },
      {
        path: "comparisons/:comparisonId",
        handle: { title: "Comparison" },
        element: <ComparisonDetailPage />,
      },
      {
        path: "executions",
        handle: { title: "AI Executions" },
        element: <ExecutionsPage />,
      },
      {
        path: "executions/:executionId",
        handle: { title: "Execution" },
        element: <ExecutionDetailPage />,
      },
      {
        path: "bulk-runs",
        handle: { title: "Bulk Runs" },
        element: <BulkRunsPage />,
      },
      {
        path: "bulk-runs/:jobId",
        handle: { title: "Bulk Run" },
        element: <BulkRunDetailPage />,
      },
      {
        path: "settings",
        handle: { title: "Settings" },
        element: <SettingsPage />,
      },
      { path: "*", handle: { title: "Not found" }, element: <NotFoundPage /> },
    ],
  },
])
