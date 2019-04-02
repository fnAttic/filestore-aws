var FilestoreUploader = (function() {

    // https://pqina.nl/filepond/docs/patterns/api/server/
    function process (fieldName, file, metadata, load, error, progress, abort) {
        const request = new XMLHttpRequest();
        const upload_request = new XMLHttpRequest();
        request.open('POST', FilestoreUploader.url + '/file');
        request.onload = function () {  // handles the retrival the presigned url for upload (preprocess)
            if (request.status >= 200 && request.status < 300) {
                const preprocess = JSON.parse(request.responseText);
                upload_request.open('PUT', preprocess.url);
                upload_request.upload.onprogress = function (e) {  // update progress of upload
                    progress(e.lengthComputable, e.loaded, e.total);
                };
                upload_request.onload = function () {  // handles the upload
                    if (upload_request.status >= 200 && upload_request.status < 300) {
                        //NOTE: upload_request.responseText is empty
                        load(preprocess.id);  // the id comes from the preprocess response
                    } else {
                        error('Failed to upload file');
                    }
                };
                upload_request.onerror = function () {
                    error('Failed to upload file');
                };
                upload_request.send(file);  // sending the file to the presigned url
            } else {
                error('Could not get the upload URL');
            }
        };
        request.onerror = function () {
            error('Could not get the upload URL');
        };
        request.setRequestHeader("Content-Type", "application/json");
        request.send(JSON.stringify({  // send request to the preprocess function
            'name': file.name  // pass the file name
        }));
        return {
            abort: function () {
                upload_request.abort();
                request.abort();
                abort();
            }
        };
    }

    function revert (uniqueFileId, load, error) {
        const request = new XMLHttpRequest();
        request.open('DELETE', FilestoreUploader.url + '/file/' + uniqueFileId);
        request.onload = function () {  // handles the delete for the file
            if (request.status >= 200 && request.status < 300) {
                load();
            } else {
                error('Could not revert the file');
            }
        };
    }

    function setup (url, rootElement) {
        this.url = url;
        this.root_element = rootElement || document;
        // initialise FilePond
        FilePond.parse(FilestoreUploader.root_element);
        FilePond.setOptions({
            server: {
                process: process,
                revert: revert
            }
        });
    }

    return {
        setup: setup
    };

}());
