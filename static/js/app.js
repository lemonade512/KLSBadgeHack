angular.module('klssignin', ['ngRoute'])
.config(function($routeProvider) {
    $routeProvider
    .when('/', {
        templateUrl:'templates/whosinclass.html',
        controller: 'WhosInClassCtrl',
        authorizationRequired: false
    })
    .when('/user-dashboard', {
        templateUrl:'templates/admin_user_dashboard.html',
        controller: 'AdminUserDashCtrl',
        authorizationRequired: true
    })
    .when('/interactions', {
        templateUrl:'templates/interactions.html',
        controller: 'InteractionCtrl',
        authorizationRequired: true
    })
    .when('/add-absence', {
        templateUrl: 'templates/add-absence.html',
        controller: 'AddAbsenceCtrl',
        authorizationRequired: true
    })
    .otherwise({
        redirectTo: '/'
    })
    ;
})
.controller('MainCtrl', function($scope) {
})
.controller('SigninCtrl', function($scope, $http) {

})
.controller('WhosInClassCtrl', function($scope, $http) {
  $scope.students = {
    present: [],
    absent: [],
    nothere: []
  };
  $http.get('/whosinclass')
  .success(function(data,status) {
    $scope.students.present = data.present || [];
    $scope.students.absent = data.absent || [];
    $scope.students.nothere = data.nothere || [];
  });

  //TODO(vishesh): make this poll the server every 5 minutes for data
  // so that it remains up to date.
})

.controller('AddAbsenceCtrl', function($scope, $http) {
  $scope.students = [];
  $http.get('/students')
  .success(function(data) {
    $scope.students = _.pluck(data, 'name');
  });

  $scope.a = {};
  $scope.submit = function(a) {
    if (!$scope.a.student || !$scope.a.startdate || !$scope.a.enddate) {
      $scope.errorMessage = 'Please fill in all the fields';
      return;
    }
    console.log(a);
    $http.post('/add-absence', {
      student: a.student,
      startdate: moment(a.startdate).format('YYYY-MM-DD'),
      enddate: moment(a.enddate).format('YYYY-MM-DD')
    }).success(function(data) {
      $scope.a = {};
    }).error(function(data,status) {
      if (status == 400) {
        $scope.errorMessage = data.message;
      }
    });
  }
})

.controller('InteractionCtrl', function($scope, $http) {
  $scope.interactions = [];
  $http.get('/interactions')
  .success(function(data) {
    $scope.interactions = data.interactions;
  });
})

.controller('AdminUserDashCtrl', function($scope, $http, $location) {
    $scope.users = [];
    $http.get("/users").success(function(data) {
        console.log("Got users");
        console.log(data);
        $scope.users = data;
    });
    $scope.students = [];
    $http.get("/students").success(function(data) {
        $scope.students = data;
        console.log($scope.students);
    });

    console.log("Users");
    console.log($scope.users);

    $scope.delete_user = function(user) {
        console.log("Deleting " + user);
        $scope.users[user].deleted = true;
        $http.put("/users", {"username":  user, "params": $scope.users[user]}).success(function() {
            $http.get("/users").success(function(data) {
                $scope.users = data;
            });
        });
    };

    $scope.create_user = function() {
        var username = $scope.new_user_name;
        var user_id = $scope.new_user_id;
        console.log("Creating " + username + " with id: " + user_id);
        $http.put("/users/create", {"username": username, "id": user_id}).success(function() {
            $scope.new_user_name = "";
            $scope.new_user_id = "";
            $http.get("/users").success(function(data) {
                $scope.users = data;
            });
        });
    };

    $scope.delete_student = function(student) {
        console.log("Deleting " + student);
        $scope.students[student].deleted = true;
        $http.put("/students", {"username": student, "params": $scope.students[student]}).success(function() {
            $http.get("/students").success(function(data) {
                $scope.students = data;
            });
        });
    };

    $scope.patch_student = function(student, param) {
        console.log("Updating " + student + " parameter: " + param);
        $http.put("/students/patch", {"username": student, "param": [param, $scope.students[student][param]]});
    };

    $scope.create_student = function() {
        var username = $scope.new_student_name;
        var student_id = $scope.new_student_id;
        var can_signin = ($scope.new_student_can_signin === undefined) ? false : true;
        var can_signout = ($scope.new_student_can_signout === undefined) ? false : true;
        console.log("Creating " + username + " with id: " + student_id);
        params = {"id": student_id, "can_signin": can_signin, "can_signout": can_signout};
        $http.put("/students/create", {"username": username, "params": params}).success(function() {
            $scope.new_student_name = "";
            $scope.new_student_id = "";
            $scope.new_student_can_signin = false;
            $scope.new_student_can_signout = false;
            $http.get("/students").success(function(data) {
                $scope.students = data;
            });
        });
    };

    $scope.new_signers = {};
    $scope.add_signer = function(name) {
        if($scope.new_signers[name] !== undefined && $scope.new_signers[name] !== "") {
            console.log("Adding " + $scope.new_signers[name] + " to authorized signers.");
            $scope.students[name].authorized.push($scope.new_signers[name]);
            $http.put("/students/add-authorized", {"username": name, "signer": $scope.new_signers[name]});
            $scope.new_signers[name] = "";
        } else {
            console.log("That is empty or undefined!");
        }
    };

    $scope.remove_signer = function(student, signer) {
        console.log("Removing " + signer + " from " + student + "'s authorized signers.");
        var i = $scope.students[student].authorized.indexOf(signer);
        if(i != -1) {
            $scope.students[student].authorized.splice(i, 1);
        }
        $http.put("/students/remove-authorized", {"username": student, "signer": signer});
    };

    $scope.new_permissions = {};
    $scope.add_permission = function(name) {
        if($scope.new_permissions[name] !== undefined && $scope.new_permissions[name] !== "") {
            console.log("Adding " + $scope.new_permissions[name] + " to permission.");
            $scope.users[name].permissions.push($scope.new_permissions[name]);
            $http.put("/users/add-permission", {"username": name, "permission": $scope.new_permissions[name]});
            $scope.new_permissions[name] = "";
        } else {
            console.log("That is empty or undefined!");
        }
    };

    $scope.remove_permission = function(user, permission) {
        console.log("Removing " + permission + " from " + user + "'s permissions.");
        var i = $scope.users[user].permissions.indexOf(permission);
        if(i != -1) {
            $scope.users[user].permissions.splice(i, 1);
        }
        $http.put("/users/remove-permission", {"username": user, "permission": permission});
    };
})
.directive('contenteditable', function() {
  return {
    restrict: 'A',
    require: 'ngModel',
    scope: false,
    transclude: false,
    link: function(scope, elm, attrs, ctrl) {
      elm.bind('keydown', function(event) {
        // esc should revert the value
        if (event.which == 27) {
          event.preventDefault();
          elm.html(ctrl.$viewValue);
          // TODO(vishesh): this isn't a full solution because
          // contenteditable could be many elements deep.
          // This only works if contenteditable is used on a leaf DOM node.
          event.target.blur();
        }
        // enter should store the value
        if (event.which == 13) {
          event.preventDefault();
          event.target.blur();
        }
      });

      // view -> model
      elm.bind('blur', function() {
        scope.$apply(function() {
          ctrl.$setViewValue(elm.text().trim());
        });
      });

      // model -> view
      ctrl.$render = function() {
        elm.html(ctrl.$viewValue);
      };
    }
  };
})
.filter('startat', function() {
  return function(input, start) {
    if(input) {
      start = +start; //parse to int
      return input.slice(start);
    }
    return [];
  };
})

.filter('time', function() {
  return function(input, infmt, fmt) {
    if (input) {
      var m = moment(input, infmt || 'YYYY-MM-DD').format(fmt || 'MMMM Do YYYY');
      return m === 'Invalid Date' ? input : m;
    }
    return input;
  };
})

.filter('transform', function() {
  return function(input, from, to) {
    if (input === from) return to || '';
    return input;
  };
})
;
