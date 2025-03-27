import { useEffect, useState } from "react";

function App() {
  const [matches, setMatches] = useState([]);

  useEffect(() => {
    // Fetch match data from API
    fetch(`http://localhost:8000/matches?date=${new URLSearchParams(window.location.search).get('date')}`) // Replace with actual API URL
      .then((response) => response.json())
      .then((data) => setMatches(data.matches)) // Extract matches array
      .catch((error) => console.error("Error fetching data:", error));
  }, []);

  return (
    <div className="container">
      <h1>Upcoming Matches</h1>
      <table>
        <thead>
          <tr>
            <th>Match</th>
            <th>Watch Link</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((match, index) => (
            <tr key={index}>
              <td>{match.team1} vs {match.team2}</td>
              <td>
                <a href={match.match_link} target="_blank" rel="noopener noreferrer">
                  Watch Now
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
