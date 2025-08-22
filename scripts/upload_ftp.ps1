
$ftp = "ftp://addictiveservers.com/"
$user = "trickconfidence"
$pass = "1kw058e_Hfh5435"
$localPath = Join-Path $PSScriptRoot ".." "ftp-data"

function Upload-FtpFolder {
    param (
        [string]$localFolder,
        [string]$remoteFolder
    )
    $items = Get-ChildItem -Path $localFolder
    foreach ($item in $items) {
        $webclient = New-Object System.Net.WebClient
        $webclient.Credentials = New-Object System.Net.NetworkCredential($user, $pass)
        if ($item.PSIsContainer) {
            # Recursively upload subfolders
            Upload-FtpFolder -localFolder $item.FullName -remoteFolder ($remoteFolder + $item.Name + "/")
        } else {
            $remoteFile = $ftp + $remoteFolder + $item.Name
            Write-Host "Uploading $($item.FullName) to $remoteFile"
            $webclient.UploadFile($remoteFile, $item.FullName)
        }
    }
}

Upload-FtpFolder -localFolder $localPath -remoteFolder ""
Write-Host "Upload complete."