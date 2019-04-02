# User guide

The application offers a small subset of the functionality of the more sophisticated and feature rich SaaS products such as [Filestack](https://www.filestack.com/) and [Uploadcare](https://uploadcare.com/).

There are two modes of operation, configured at deployment time:

1. Uploaded files are stored immediately.
1. Uploaded files are deleted after expiry unless specifically stored with an API call.

## Storing files
How to choose between the two modes of operations?

Explicitely storing the files after a temporary upload is convenient solution against the risks of unlimited file uploads.
In either case your users will be able to upload files to your service, and ultimately to S3.

If the uploads are stored immediately you can decide which ones to keep or remove at any point in your application.

If uploads are temporary, the system will remove them automatically after a period of time, unless the ```store``` function is called on the upload.
There is a scheduled check for expired uploads which deletes any un-stored upload.

### A typical scenario with expicit request to store files

1. User retrieves web page with a form to upload file
1. User uploads the file via the browser client
1. User submits form
1. Backend receives the form, including the identifier (id) for the uploaded file
1. Backend processes the form
1. Backend makes an API call to store the file

### Same as above but the user abandons the web page or form

1. User retrieves web page with a form to upload file
1. User uploads the file via the browser client
1. User abandons the web page and form
1. The Filestore application regularly checks for files not stored after a period
1. The Filestore deletes the file, marks record as deleted with a timestamp

## API
The Filestore application is a set of API-s available to any HTTP REST capable client.

### HTTP POST /file
Request a signed URL where a file can be uploaded.

#### Request
* ```content-type``` : application/json
* ```body```
    * name : (String) (Required) Name of the file uploaded with extension

#### Response HTTP 200 
* ```content-type``` : application/json
* ```body```
    * id : (String) The identifier (id) for the uploaded file
    * url : (String) The URL where the file can be uploaded to (PUT)

### HTTP POST \[upload URL\]
Send the file to the upload URL.

### HTTP PUT /files
Store file(s) that were uploaded temporarily.

Note that there is a soft limit set on the number of files to store in one request.

#### Request
* ```x-api-key``` : [YOUR API KEY]
* ```content-type``` : application/json
* ```body```
    * array
        * (String) The stored file identifier (id)

#### Response HTTP 200 
* ```content-type``` : application/json
* ```body```
    * array
        * (String) The file identifier (id)

This API returns *HTTP 400* if the deployment has the "store immediately" configured. 

### HTTP POST /files
Get file details, including pre-signed download URL.

By default the response only includes stored and non-deleted files, use query parameters to include deleted and non-stored files.

The download URL is only available for stored and non-deleted files.

#### Request
* optional query parameters
    * deleted=yes : include information on deleted files
    * nonstored=yes : include information on non-stored files
* ```x-api-key``` : [YOUR API KEY]
* ```content-type``` : application/json
* ```body```
    * array
        * (String) The file identifier (id) to get details for

#### Response HTTP 200 
* ```content-type``` : application/json
* ```body```
    * array
        * id : (String) File identifier (id)
        * url : (String) File download URL
        * name : (String) File name
        * type : (String) File mime-type
        * size : (Number) File size 

### HTTP DELETE /files
Delete file(s).
Note that the uploaded file gets deleted, but the file information is retained with a ```deleted_at``` timestamp.

#### Request
* ```x-api-key``` : [YOUR API KEY]
* ```content-type``` : application/json
* ```body```
    * array
        * (String) The file identifier (id) to delete

#### Response HTTP 200
* ```content-type``` : application/json
* ```body```
    * array
        * (String) The deleted file identifier (id)

### HTTP GET \[download URL\]
Retrieve the file from the download URL. 
The response will include the headers for ```content-type``` and ```content-disposition```.

## Client application

The Filestore implementation includes an example web page (with a form) and a JavaScript wrapper (uploader.js) for the [FilePond](https://pqina.nl/filepond/) library.
 