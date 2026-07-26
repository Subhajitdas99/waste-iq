import { Mail, Phone, MapPin, Github, Linkedin, Twitter } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { SeoHead } from "@/components/seo/SeoHead";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { ContactForm } from "@/components/contact/ContactForm";

const socialLinks = [
  { icon: <Twitter size={20} />, label: "Twitter", href: "https://twitter.com" },
  { icon: <Github size={20} />, label: "GitHub", href: "https://github.com" },
  { icon: <Linkedin size={20} />, label: "LinkedIn", href: "https://linkedin.com" },
];

export function ContactPage() {
  return (
    <>
      <SeoHead
        title="Contact Us"
        description="Get in touch with the Waste-IQ team for partnerships, support, or municipal inquiries."
        path="/contact"
      />

      <SectionContainer className="pt-32 pb-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
              Contact Us
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Have questions about Waste-IQ? Want to implement our solution in
              your city? We&apos;d love to hear from you.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-start">
            <div className="space-y-6">
              <Card className="bg-muted/30 border-none shadow-none">
                <CardContent className="p-6 flex items-start gap-4">
                  <div className="p-3 bg-primary/10 text-primary rounded-full shrink-0">
                    <Mail className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-lg mb-1">Email Us</h2>
                    <p className="text-muted-foreground mb-2 text-sm">
                      Our friendly team is here to help.
                    </p>
                    <a
                      href="mailto:hello@waste-iq.example.com"
                      className="font-medium text-primary hover:underline"
                    >
                      hello@waste-iq.example.com
                    </a>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-muted/30 border-none shadow-none">
                <CardContent className="p-6 flex items-start gap-4">
                  <div className="p-3 bg-primary/10 text-primary rounded-full shrink-0">
                    <MapPin className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-lg mb-1">Office</h2>
                    <p className="text-muted-foreground mb-2 text-sm">
                      Come say hello at our headquarters.
                    </p>
                    <address className="not-italic font-medium text-sm">
                      100 Eco Innovation Way
                      <br />
                      San Francisco, CA 94105
                    </address>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-muted/30 border-none shadow-none">
                <CardContent className="p-6 flex items-start gap-4">
                  <div className="p-3 bg-primary/10 text-primary rounded-full shrink-0">
                    <Phone className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-lg mb-1">Phone</h2>
                    <p className="text-muted-foreground mb-2 text-sm">
                      Mon-Fri from 8am to 5pm.
                    </p>
                    <a
                      href="tel:+15550000000"
                      className="font-medium text-primary hover:underline"
                    >
                      +1 (555) 000-0000
                    </a>
                  </div>
                </CardContent>
              </Card>

              <div>
                <h2 className="font-semibold text-lg mb-3">Follow Us</h2>
                <div className="flex items-center gap-4">
                  {socialLinks.map((link) => (
                    <a
                      key={link.label}
                      href={link.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={link.label}
                      className="p-3 rounded-full bg-muted text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      {link.icon}
                    </a>
                  ))}
                </div>
              </div>

              <div
                className="rounded-xl border bg-muted/30 overflow-hidden h-48 flex items-center justify-center"
                aria-label="Map placeholder"
              >
                <div className="text-center text-muted-foreground">
                  <MapPin className="h-8 w-8 mx-auto mb-2 opacity-50" aria-hidden="true" />
                  <p className="text-sm font-medium">Google Map Placeholder</p>
                  <p className="text-xs mt-1">100 Eco Innovation Way, San Francisco</p>
                </div>
              </div>
            </div>

            <Card className="shadow-lg">
              <CardContent className="p-8">
                <h2 className="text-2xl font-bold mb-6">Send us a message</h2>
                <ContactForm />
              </CardContent>
            </Card>
          </div>
        </div>
      </SectionContainer>
    </>
  );
}
