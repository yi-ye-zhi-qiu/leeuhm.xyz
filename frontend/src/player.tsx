import { useQuery } from "@tanstack/react-query"

function PlayerData() {
  const { isPending, error, data } = useQuery({
    queryKey: ["player"],
    queryFn: () => fetch("/api/player").then((res) => res.json())
  })

  if (isPending) return "Loading..."

  if (error) return error.message

  return <div>
    <p>{data.userName}</p>
  </div>
}

function MatchData() {
  const { isPending, error, data } = useQuery({
    queryKey: ["matchData"],
    queryFn: () => fetch("/api/matchData").then((res) => res.json())
  })

  if (isPending) return "Loading..."

  if (error) return error.message

  return <div>
    <p>{data.length} matches from this player</p>
  </div>
}

function MatchDetails() {
  const { isPending, error, data } = useQuery({
    queryKey: ["matchDetails"],
    queryFn: () => fetch("/api/matchDetails").then((res) => res.json())
  })

  if (isPending) return "Loading..."

  if (error) return error.message

  return <div>
    <p>match details here</p>
  </div>
}



function Player() {
  return <>
    <PlayerData />
    <MatchData />
    <MatchDetails />
  </>
}

export default function Player
