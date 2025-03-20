# PowerShell script to export player rankings sorted by compscore
# Save this as export_player_rankings.ps1

# Configuration
$serverName = "localhost"
$databaseName = "NRFI"
$downloadsFolder = [Environment]::GetFolderPath("UserProfile") + "\Downloads"
$outputFile = "$downloadsFolder\player_rankings_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"

# SQL query - select required fields in specified order and sort by compscore
$query = @"
SELECT 
    newID, 
    Name, 
    pos AS Position, 
    ADP, 
    team AS Team 
FROM 
    [NRFI].[dbo].[BBdkppgH_New] 
ORDER BY 
    compscore DESC
"@

# Create connection string
$connectionString = "Server=$serverName;Database=$databaseName;Integrated Security=True;"

# Create SQL connection
$connection = New-Object System.Data.SqlClient.SqlConnection
$connection.ConnectionString = $connectionString

try {
    # Open connection
    $connection.Open()
    Write-Host "Connected to database successfully."
    
    # Setup command
    $command = New-Object System.Data.SqlClient.SqlCommand
    $command.Connection = $connection
    $command.CommandText = $query
    
    # Execute and export to CSV
    $adapter = New-Object System.Data.SqlClient.SqlDataAdapter $command
    $dataset = New-Object System.Data.DataSet
    $adapter.Fill($dataset)
    
    # Export to CSV
    $dataset.Tables[0] | Export-Csv -Path $outputFile -NoTypeInformation
    
    Write-Host "Data exported successfully to: $outputFile"
    
    # Open the downloads folder
    Invoke-Item (Split-Path $outputFile)
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
finally {
    # Close connection
    if ($connection.State -eq 'Open') {
        $connection.Close()
        Write-Host "Database connection closed."
    }
}