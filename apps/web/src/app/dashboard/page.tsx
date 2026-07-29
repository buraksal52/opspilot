import { BackendHealth } from "@/components/backend-health";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          OpsPilot investigates business questions using structured and unstructured company data.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Backend Connectivity</CardTitle>
          <CardDescription>Live status of the FastAPI health endpoint.</CardDescription>
        </CardHeader>
        <CardContent>
          <BackendHealth />
        </CardContent>
      </Card>
    </div>
  );
}
