var express = require('express'),
    mpo = require('./routes/mpo');
 
var app = express();
var version = '/v0';

//Middleware: Allows cross-domain requests (CORS)
var allowCrossDomain = function(req, res, next) {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE');
    res.header('Access-Control-Allow-Headers', 'Content-Type');

    next();
}

app.configure(function () {
    app.use(express.logger('dev'));     /* 'default', 'short', 'tiny', 'dev' */
    app.use(express.bodyParser());
    app.use(allowCrossDomain);
});
 
//Objects
app.get(version+'/dataobject', mpo.DataObjectFindAll);
app.get(version+'/dataobject/:id', mpo.DataObjectFindById);
app.post(version+'/dataobject', mpo.DataObjectAdd);
//app.put(version+'/dataobject/:id', mpo.DataObjectUpdate);
//app.delete(version+'/dataobject/:id', mpo.DataObjectDelete);
  
app.get(version+'/workflow', mpo.WorkflowFindAll);
app.get(version+'/workflow/:id', mpo.WorkflowFindById);
app.get(version+'/workflow/:id/graph', mpo.WorkflowGraphById);
app.get(version+'/workflow/:id/alias', mpo.WorkflowFindAlias);
app.get(version+'/workflow/alias/:user/:name/:seq', mpo.WorkflowFindByAlias);

app.post(version+'/workflow', mpo.WorkflowAdd);

app.get(version+'/connection', mpo.ConnectionFindAll);
app.get(version+'/connection/:id', mpo.ConnectionFindById);
app.post(version+'/connection', mpo.ConnectionAdd);

app.get(version+'/activity', mpo.ActivityFindAll);
app.get(version+'/activity/:id', mpo.ActivityFindById);
app.post(version+'/activity', mpo.ActivityAdd);

app.get(version+'/comment', mpo.CommentFindAll);
app.get(version+'/comment/:id', mpo.CommentFindById);
app.post(version+'/comment', mpo.CommentAdd);

app.get(version+'/metadata', mpo.MetadataFindAll);
app.get(version+'/metadata/:id', mpo.MetadataFindById);
app.post(version+'/metadata', mpo.MetadataAdd);
 
app.get(version+'/object/:id', mpo.ObjectFindById);

app.listen(3001);
console.log('Listening on port 3001...');


