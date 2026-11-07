import { createBrowserRouter } from "react-router"

import { AppShell } from "@/app/AppShell"
import { NotFoundPage, PlaceholderPage } from "@/app/PlaceholderPage"
import { ComparePage } from "@/features/compare/ComparePage"
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
        element: <PlaceholderPage phase={14} what="The dashboard" />,
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
        element: <PlaceholderPage phase={12} what="Comparison history" />,
      },
      {
        path: "comparisons/:comparisonId",
        handle: { title: "Comparison" },
        element: <PlaceholderPage phase={12} what="Comparison detail" />,
      },
      {
        path: "executions",
        handle: { title: "AI Executions" },
        element: <PlaceholderPage phase={11} what="The execution log" />,
      },
      {
        path: "executions/:executionId",
        handle: { title: "Execution" },
        element: <PlaceholderPage phase={11} what="Execution detail" />,
      },
      {
        path: "settings",
        handle: { title: "Settings" },
        element: <PlaceholderPage phase={15} what="The settings page" />,
      },
      { path: "*", handle: { title: "Not found" }, element: <NotFoundPage /> },
    ],
  },
])
