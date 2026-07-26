import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight, Recycle, Truck, Leaf } from "lucide-react";
import { Button } from "@/components/ui/button";

function AnimatedBackground() {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-background to-background" />
      <motion.div
        className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-primary/20 blur-3xl"
        animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl"
        animate={{ scale: [1.2, 1, 1.2], opacity: [0.2, 0.4, 0.2] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10 mix-blend-overlay" />
    </div>
  );
}

function HeroIllustration() {
  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 0.3 }}
      className="relative hidden lg:block"
      aria-hidden="true"
    >
      <div className="relative w-full max-w-lg mx-auto">
        <div className="absolute inset-0 bg-gradient-to-tr from-primary/30 to-cyan-500/30 rounded-3xl transform rotate-6 blur-sm" />
        <div className="relative bg-card/80 backdrop-blur-md border rounded-3xl p-8 shadow-2xl space-y-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center">
              <Leaf className="h-5 w-5 text-primary" />
            </div>
            <div>
              <div className="h-3 w-32 bg-muted rounded" />
              <div className="h-2 w-20 bg-muted/60 rounded mt-1" />
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-primary/5 border border-primary/10">
              <Recycle className="h-5 w-5 text-primary shrink-0" />
              <div className="flex-1">
                <div className="h-2.5 w-full bg-primary/20 rounded" />
                <div className="h-2 w-3/4 bg-primary/10 rounded mt-1.5" />
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-xl bg-cyan-500/5 border border-cyan-500/10">
              <Truck className="h-5 w-5 text-cyan-500 shrink-0" />
              <div className="flex-1">
                <div className="h-2.5 w-full bg-cyan-500/20 rounded" />
                <div className="h-2 w-2/3 bg-cyan-500/10 rounded mt-1.5" />
              </div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {["2M+", "500k+", "1.2k+"].map((val) => (
              <div key={val} className="text-center p-3 rounded-xl bg-muted/50">
                <div className="text-lg font-bold text-primary">{val}</div>
                <div className="h-1.5 w-8 bg-muted rounded mx-auto mt-1" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
      <AnimatedBackground />

      <div className="container mx-auto px-4 md:px-6">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-8 text-center lg:text-left"
          >
            <div className="inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold bg-primary/10 text-primary">
              <span className="flex h-2 w-2 rounded-full bg-primary mr-2 animate-pulse" />
              Join the Circular Economy
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-tight">
              Smarter Waste Management for a{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-cyan-500">
                Cleaner Planet
              </span>
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground max-w-xl mx-auto lg:mx-0 leading-relaxed">
              Waste-IQ is the all-in-one digital platform connecting citizens,
              verified collectors, and recycling dealers to transform waste into
              resources.
            </p>

            <div className="flex flex-col sm:flex-row justify-center lg:justify-start gap-4">
              <Link to="/register">
                <Button
                  size="lg"
                  className="w-full sm:w-auto text-lg h-14 px-8 rounded-full shadow-lg hover:shadow-primary/25 transition-all"
                >
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link to="/features">
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto text-lg h-14 px-8 rounded-full bg-background/50 backdrop-blur-sm"
                >
                  Explore Features
                </Button>
              </Link>
            </div>
          </motion.div>

          <HeroIllustration />
        </div>
      </div>
    </section>
  );
}
