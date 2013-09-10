
var mongo = require('mongodb');
 
var Server = mongo.Server,
    Db = mongo.Db,
    BSON = mongo.BSONPure;
 
var server = new Server('localhost', 27017, {auto_reconnect: true});
db = new Db('mpo', server);

/*--------------------------------------------------------------------------------------------------------------------*/
// Populate database with sample data -- Only used once: the first time the application is started.
// You'd typically not find this code in a real-life app, since the database would already exist.
var populateMPO = function() {
 
    var dataobjectTemplate = [
    {
        name: "objectTemplate",
        time: new Date().getTime(),
        user: "admin",
        workflow: 0,
	description:"Fields template for Data Objects",
	uri: 0,
	uritype: "unused"
    }];
 
    db.collection('dataobject', function(err, collection) {
        collection.insert(dataobjectTemplate, {safe:true}, function(err, result) {});
    });

    var activityTemplate = [
    {
        name: "activityTemplate",
        time: new Date().getTime(),
        user: "admin",
        workflow: 0,
	description:"Fields template for Activities",
	uri: 0,
	uritype: "unused"
    }];
 
    db.collection('activity', function(err, collection) {
        collection.insert(activityTemplate, {safe:true}, function(err, result) {});
    });

    var connectionTemplate = [
    {
        name: "connectionTemplate",
        time: new Date().getTime(),
        user: "admin",
        workflow: 0,
	parent_id:0,
	child_id:0,
	description:"Fields template for connections",
	uri: 0,
	uritype: "unused"
    }];
 
    db.collection('connection', function(err, collection) {
        collection.insert(connectionTemplate, {safe:true}, function(err, result) {});
    });

    var userTemplate = [
    {
        name: "Template",
        time: new Date().getTime(),
        user: "admin",
	description:"Fields template for Data Objects",
	uri: 0,
	uritype: "unused"
    }];
 
    db.collection('user', function(err, collection) {
        collection.insert(userTemplate, {safe:true}, function(err, result) {});
    });


    var workflowTemplate = [
    {
        name: "Template",
        time: new Date().getTime(),
        user: "admin",
	description:"Fields template for workflows",
	uri: 0,
	uritype: "unused"
    }];
 
    db.collection('workflow', function(err, collection) {
        collection.insert(workflowTemplate, {safe:true}, function(err, result) {});
    });

    var commentTemplate = [
    {
        name: "Template",
        time: new Date().getTime(),
        user: "admin",
	text:"Fields template for Data Objects",
	objectid: 0,
	uritype: "unused"
    }];
 
    db.collection('comment', function(err, collection) {
        collection.insert(commentTemplate, {safe:true}, function(err, result) {});
    });

    var metadataTemplate = [
    {
        name: "Template",
        time: new Date().getTime(),
        user: "admin",
        value:"Fields template for Data Objects",
	key:"null",
        objectid: 0,
        uritype: "unused"
    }];

    db.collection('metadata', function(err, collection) {
        collection.insert(commentTemplate, {safe:true}, function(err, result) {});
    });



};

db.open(function(err, db) {
    if(!err) {
        console.log("Connected to 'mpo' database");
        db.collection('dataobject', {safe:true}, function(err, collection) {
	    collection.count(function(err, count) {
		if (count==0) {
                    console.log("The 'dataobject' collection doesn't exist. Creating it with sample data..."+err);
		    console.log(count);
                    populateMPO(); 
		}
	    });
        });
    }
});
 
exports.DataObjectFindById = function(req, res) {
    var id = req.params.id;
    console.log('Retrieving dataobject: ' + id);
    db.collection('dataobject', function(err, collection) {
        collection.findOne({'_id':new BSON.ObjectID(id)}, function(err, item) {
            res.send(item);
        });
    });
};
 
exports.DataObjectFindAll = function(req, res) {
    db.collection('dataobject', function(err, collection) {
        collection.find().toArray(function(err, items) {
            res.send(items);
        });
    });
};

 
exports.DataObjectAdd= function(req, res) {
    var mpo = req.body;
    mpo.time = new Date().getTime();
    console.log('Adding dataobject: ' + JSON.stringify(mpo));
    db.collection('dataobject', function(err, collection) {
        collection.insert(mpo, {safe:true}, function(err, result) {
            if (err) {
                res.send({'error':'An error has occurred'});
            } else {
                console.log('Success: ' + JSON.stringify(result[0]));
                res.send(result[0]);
            }
        });
    });
}
//------------------------------------------------------------------------
 
exports.ConnectionFindById = function(req, res) {
    var id = req.params.id;
    console.log('Retrieving connection: ' + id);
    db.collection('connection', function(err, collection) {
        collection.findOne({'_id':new BSON.ObjectID(id)}, function(err, item) {
            res.send(item);
        });
    });
};
 
exports.ConnectionFindAll = function(req, res) {
    var workid = req.query.workflow_id;
    console.log(req.query);
//Would be better to construct query string and then have the db commands.
    if (workid) {
		db.collection('connection', function(err, collection) {
		    collection.find({"workflow_id":workid}).toArray(function(err, items) {
			res.send(items);
		    });
		});

            } else {
		db.collection('connection', function(err, collection) {
		    collection.find().toArray(function(err, items) {
			res.send(items);
		    });
		});
            }
};

 
exports.ConnectionAdd= function(req, res) {
    var mpo = req.body;
    mpo.time = new Date().getTime();
    console.log('Adding connection: ' + JSON.stringify(mpo));
    db.collection('connection', function(err, collection) {
        collection.insert(mpo, {safe:true}, function(err, result) {
            if (err) {
                res.send({'error':'An error has occurred'});
            } else {
                console.log('Success: ' + JSON.stringify(result[0]));
                res.send(result[0]);
            }
        });
    });
}


//------------------------------------------------------------------------
 
exports.WorkflowFindById = function(req, res) {
    var id = req.params.id;
    var compid = req.query.alias; //or shortcut or compid
    console.log('Retrieving workflow: ' + id);

    db.collection('workflow', function(err, collection) {
        collection.findOne({'_id':new BSON.ObjectID(id)}, function(err, item) {
	    console.log('Retrieving shortcut for: ' + compid);
	    if (compid == ""){
		console.log('Retrieving shortcut for: ' + id);
		res.send({"alias":item["user"]+item["name"]});
	    } else{
		res.send(item);
	    }
        });
    });
};


exports.WorkflowFindByAlias = function(req, res) {
    var id = req.params.id;
    var user = req.params.user,
        name = req.params.name, 
        seq = parseInt(req.params.seq, 10);
    console.log('Retrieving workflow: ' + user + name + seq);

    db.collection('workflow', function(err, collection) {
        collection.findOne({'user':user, 'name':name, "composite_seq":seq}, function(err, item) {
		res.send(item);
        });
    });
};

exports.WorkflowFindAlias = function(req, res) {
    var id = req.params.id;
    console.log('Retrieving alias: ' + id);
    db.collection('workflow', function(err, collection) {
        collection.findOne({'_id':new BSON.ObjectID(id)}, function(err, item) {
	    console.log('Retrieving shortcut for: ' + id);
	    res.send({"alias":item["user"]+"/"+item["name"]+"/"+item["composite_seq"]});
        });
    });
};

exports.ObjectFindById =  function(req, res) {
    var id = req.params.id;
    console.log('Retrieving Object: ' + id);
    var count = 5;
    var nodeinfo = [];

    var doneFn = function(results) {
	nodeinfo = nodeinfo.concat(results);
	count--;
	if( count <= 0 ) 
	    res.send({"object":nodeinfo,
		      "uri":"http://"+req.header('host')+req.url});
    };

    //run the count=5 queries over the collections that could have our IDs
    var ids =  [new BSON.ObjectID(id)]; //runQueryID expects and array of values
    runQueryID ('workflow', ids, doneFn);
    runQueryID ('activity', ids, doneFn);
    runQueryID ('dataobject', ids, doneFn);
    runQueryID ('metadata', ids, doneFn);
    runQueryID ('comment', ids, doneFn);
};

function runQueryID (mycollection, ids, nextFn) {
    //perform query for BSON.ObjectID id in mycollection, forward result to nextFN
    db.collection(mycollection).find({'_id': {$in : ids} }).toArray(function(err, doc) {
	var r = [];
	if (doc!=null){
	    for (var i=0; i<doc.length; i++){
		doc[i].type=mycollection;
		r[r.length] = doc[i];
	    }
	}
	nextFn(r);
    });
}

exports.WorkflowGraphById = function(req, res) {
    var id = req.params.id;
    console.log('Retrieving workflow graph: ' + id);
    db.collection('connection', function(err, collection) {
        collection.find({"workflow_id":id}).toArray(function(err, connections) {
	    if(err){
		console.log('WorkflowGraphById'+err);
	    }

	    else{
//make unique list of parent/child ids
		var temp = {}, ids=[];
		for (var i=0; i<connections.length; i++){
		    temp[connections[i].parent_id] = true;
		    temp[connections[i].child_id] = true;}
		for (var id in temp) ids[ids.length]=new BSON.ObjectID(id);

		var count = 3;
		var nodeinfo = [];
		var doneFn = function(results) {
		    nodeinfo = nodeinfo.concat(results);
		    count--;

		    if( count <= 0 ) 
			res.send({'graph':connections,'nodes':nodeinfo,
				  'uri':'http://'+req.header('host')+req.url});

		};

		//run the count=3 queries over the collections that could have our IDs
		runQueryID ('workflow', ids, doneFn);
		runQueryID ('activity', ids, doneFn);
		runQueryID ('dataobject', ids, doneFn);
	    }
	});
    });
};

 
exports.WorkflowFindAll = function(req, res) {
    var user = req.query.user;
    var qry = {};
    var alias = req.query.alias;

    if (user) {
	qry["user"]=user;
	}
    
    if (alias) {
	palias=alias.split("/");
	qry["user"]=palias[0];
	qry["name"]=palias[1];
	qry["composite_seq"]=parseInt(palias[2],10);
	}

    db.collection('workflow', function(err, collection) {
        collection.find(qry).toArray(function(err, items) {
            res.send(items);
        });
    });
};

 
exports.WorkflowAdd= function(req, res) {
    var mpo = req.body;
    mpo.time = new Date().getTime();

    console.log('Adding workflow: ' + JSON.stringify(mpo));
    db.collection('workflow', function(err, collection) {
	console.log('Adding workflow, aggregate: ' + mpo.user+" "+mpo.name);
//Collect all records matching user and name and selects the one with the largest composite_seq
	collection.aggregate( 
	    {$match: {'user' : mpo.user, 'name':mpo.name }} , 
            {$group: {_id:{name:"$name",user:"$user"}, seqn : { $max:'$composite_seq' } }},
	    function(err,result) { console.log(result);
//If no records are found, composite_seq=1, otherwise composite_seq=max(composite_seq)+1
		var count=0;
		if (result.length==1){
		       count=result[0].seqn;}
		var nextseq=count+1;
		console.log('Adding workflow, aggregate: ' + nextseq);
		mpo.composite_seq=nextseq;

        collection.insert(mpo, {safe:true}, function(err, result) {
            if (err) {
                res.send({'error':'An error has occurred'});
            } else {
                console.log('Success: ' + JSON.stringify(result[0]));
		r=result[0];
                res.send(r);
            }
        });
	    });
    });
}
//------------------------------------------------------------------------
 
exports.CommentFindById = function(req, res) {
    var id = req.params.id;
    console.log('Retrieving comment: ' + id);
    db.collection('comment', function(err, collection) {
        collection.findOne({'_id':new BSON.ObjectID(id)}, function(err, item) {
            res.send(item);
        });
    });
};
 
exports.CommentFindAll = function(req, res) {
    db.collection('comment', function(err, collection) {
        collection.find().toArray(function(err, items) {
            res.send(items);
        });
    });
};

 
exports.CommentAdd= function(req, res) {
    var mpo = req.body;
    mpo.time = new Date().getTime();
    console.log('Adding comment: ' + JSON.stringify(mpo));
    db.collection('comment', function(err, collection) {
        collection.insert(mpo, {safe:true}, function(err, result) {
            if (err) {
                res.send({'error':'An error has occurred'});
            } else {
                console.log('Success: ' + JSON.stringify(result[0]));
                res.send(result[0]);
            }
        });
    });
}


 
exports.MetadataFindById = function(req, res) {
    var id = req.params.id;
    console.log('Retrieving metadata: ' + id);
    db.collection('metadata', function(err, collection) {
        collection.findOne({'_id':new BSON.ObjectID(id)}, function(err, item) {
            res.send(item);
        });
    });
};
 
exports.MetadataFindAll = function(req, res) {
    db.collection('metadata', function(err, collection) {
        collection.find().toArray(function(err, items) {
            res.send(items);
        });
    });
};


exports.MetadataAdd= function(req, res) {
    var mpo = req.body;
    mpo.time = new Date().getTime();
    console.log('Adding metadata: ' + JSON.stringify(mpo));
    db.collection('metadata', function(err, collection) {
        collection.insert(mpo, {safe:true}, function(err, result) {
            if (err) {
                res.send({'error':'An error has occurred'});
            } else {
                console.log('Success: ' + JSON.stringify(result[0]));
                res.send(result[0]);
            }
        });
    });
}
//------------------------------------------------------------------------
exports.ActivityFindById = function(req, res) {
    var id = req.params.id;
    console.log('Retrieving activity: ' + id);
    db.collection('activity', function(err, collection) {
        collection.findOne({'_id':new BSON.ObjectID(id)}, function(err, item) {
            res.send(item);
        });
    });
};
 
exports.ActivityFindAll = function(req, res) {
    db.collection('activity', function(err, collection) {
        collection.find().toArray(function(err, items) {
            res.send(items);
        });
    });
};

 
exports.ActivityAdd= function(req, res) {
    var mpo = req.body;
    mpo.time = new Date().getTime();
    console.log('Adding activity: ' + JSON.stringify(mpo));
    db.collection('activity', function(err, collection) {
        collection.insert(mpo, {safe:true}, function(err, result) {
            if (err) {
                res.send({'error':'An error has occurred'});
            } else {
                console.log('Success: ' + JSON.stringify(result[0]));
                res.send(result[0]);
            }
        });
    });
}
//------------------------------------------------------------------------

exports.Mpo = function(req, res) {
    var mpo = req.body;
    mpo.time = new Date().getTime();
    console.log('Adding mpo: ' + JSON.stringify(mpo));
    db.collection('mpos', function(err, collection) {
        collection.insert(mpo, {safe:true}, function(err, result) {
            if (err) {
                res.send({'error':'An error has occurred'});
            } else {
                console.log('Success: ' + JSON.stringify(result[0]));
                res.send(result[0]);
            }
        });
    });
}
 
exports.updateMpo = function(req, res) {
    var id = req.params.id;
    var mpo = req.body;
    console.log('Updating mpo: ' + id);
    console.log(JSON.stringify(mpo));
    db.collection('mpos', function(err, collection) {
        collection.update({'_id':new BSON.ObjectID(id)}, mpo, {safe:true}, function(err, result) {
            if (err) {
                console.log('Error updating mpo: ' + err);
                res.send({'error':'An error has occurred'});
            } else {
                console.log('' + result + ' document(s) updated');
                res.send(mpo);
            }
        });
    });
}
 
exports.deleteMpo = function(req, res) {
    var id = req.params.id;
    console.log('Deleting mpo: ' + id);
    db.collection('mpos', function(err, collection) {
        collection.remove({'_id':new BSON.ObjectID(id)}, {safe:true}, function(err, result) {
            if (err) {
                res.send({'error':'An error has occurred - ' + err});
            } else {
                console.log('' + result + ' document(s) deleted');
                res.send(req.body);
            }
        });
    });
}
 
