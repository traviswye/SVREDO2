// src/pages/PlayerDetails.js
import React from 'react';
import { useParams } from 'react-router-dom';

function UserDetails() {
  let { id } = useParams();

  return (
    <div>
      <h1>User Details for {id}</h1>
      {/* Add detailed stats and visualizations here */}
    </div>
  );
}

export default UserDetails;
