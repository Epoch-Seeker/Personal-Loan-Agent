import { useEffect, useState } from "react";

interface HelpSection {
  id: string;
  title: string;
  items: string[];
}

interface HelpResponse {
  title: string;
  sections: HelpSection[];
}

const HelpModal = () => {
  const [data, setData] = useState<HelpResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/api/help")
      .then((res) => {
        if (!res.ok) {
          throw new Error("Failed to fetch help content");
        }
        return res.json();
      })
      .then((json) => setData(json))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading help...</p>;
  }

  if (error) {
    return <p className="text-sm text-red-500">{error}</p>;
  }

  if (!data) {
    return <p>No help data available.</p>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">{data.title}</h2>

      {data.sections.map((section) => (
        <div key={section.id} className="space-y-1">
          <h3 className="font-medium">{section.title}</h3>
          <ul className="list-disc ml-5 text-sm text-muted-foreground">
            {section.items.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
};

export default HelpModal;
