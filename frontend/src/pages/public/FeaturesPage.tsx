import {
  CheckCircle2,
  Users,
  Truck,
  Factory,
  BarChart3,
  Calendar,
  Camera,
  MapPin,
  Bell,
  ClipboardList,
  TrendingUp,
  ShoppingCart,
  Package,
  History,
  Shield,
  Settings,
  FileText,
  Globe,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeoHead } from "@/components/seo/SeoHead";
import { SectionContainer } from "@/components/layout/SectionContainer";

const roleFeatures = [
  {
    title: "For Citizens",
    icon: <Users className="h-8 w-8 text-primary" />,
    iconBg: "bg-primary/10",
    features: [
      { icon: <Calendar className="h-5 w-5" />, text: "Easy pickup scheduling from mobile or desktop" },
      { icon: <Camera className="h-5 w-5" />, text: "Upload images of waste for better sorting" },
      { icon: <MapPin className="h-5 w-5" />, text: "Real-time tracking of collector ETA" },
      { icon: <TrendingUp className="h-5 w-5" />, text: "View historical impact and eco-points" },
    ],
  },
  {
    title: "For Collectors",
    icon: <Truck className="h-8 w-8 text-cyan-500" />,
    iconBg: "bg-cyan-500/10",
    features: [
      { icon: <Globe className="h-5 w-5" />, text: "Optimized routing using intelligent algorithms" },
      { icon: <Bell className="h-5 w-5" />, text: "Instant notifications for nearby pickups" },
      { icon: <ClipboardList className="h-5 w-5" />, text: "Digital workflow to update pickup status" },
      { icon: <TrendingUp className="h-5 w-5" />, text: "Performance and earnings tracking" },
    ],
  },
  {
    title: "For Dealers & Recyclers",
    icon: <Factory className="h-8 w-8 text-green-500" />,
    iconBg: "bg-green-500/10",
    features: [
      { icon: <ShoppingCart className="h-5 w-5" />, text: "Access to a verified digital marketplace" },
      { icon: <Package className="h-5 w-5" />, text: "Browse aggregated waste lots by category" },
      { icon: <CheckCircle2 className="h-5 w-5" />, text: "Reserve and purchase inventory directly" },
      { icon: <History className="h-5 w-5" />, text: "Track purchase history and supply chain" },
    ],
  },
  {
    title: "For Municipalities",
    icon: <BarChart3 className="h-8 w-8 text-indigo-500" />,
    iconBg: "bg-indigo-500/10",
    features: [
      { icon: <BarChart3 className="h-5 w-5" />, text: "Comprehensive dashboard of city-wide waste flows" },
      { icon: <Shield className="h-5 w-5" />, text: "Manage and verify collectors and dealers" },
      { icon: <Settings className="h-5 w-5" />, text: "Set pricing rules and material categories" },
      { icon: <FileText className="h-5 w-5" />, text: "Generate detailed sustainability reports" },
    ],
  },
];

export function FeaturesPage() {
  return (
    <>
      <SeoHead
        title="Features"
        description="Explore the comprehensive features of Waste-IQ for citizens, collectors, dealers, and municipalities."
        path="/features"
      />

      <SectionContainer className="pt-32 pb-20">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
            Platform Features
          </h1>
          <p className="text-xl text-muted-foreground">
            A comprehensive suite of tools tailored for every participant in the
            circular economy.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {roleFeatures.map((role) => (
            <Card
              key={role.title}
              className="border bg-card/50 backdrop-blur-sm shadow-sm hover:shadow-md transition-shadow"
            >
              <CardHeader>
                <div className={`mb-4 p-3 rounded-xl w-fit ${role.iconBg}`}>
                  {role.icon}
                </div>
                <CardTitle className="text-2xl">{role.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-4">
                  {role.features.map((feature) => (
                    <li key={feature.text} className="flex items-start gap-3">
                      <span className="text-primary shrink-0 mt-0.5">
                        {feature.icon}
                      </span>
                      <span className="text-muted-foreground">{feature.text}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </SectionContainer>
    </>
  );
}
