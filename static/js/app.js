angular.module('klssignin', ['ngRoute'])
.config(function($routeProvider) {
    $routeProvider
    .when('/', {
        templateUrl:'templates/signin.html',
        controller: 'SigninCtrl'
    })
    .when('/admin/user-dashboard', {
        templateUrl:'templates/admin_user_dashboard.html',
        controller: 'AdminUserDashCtrl'
    })
    .when('/whosinclass', {
        templateUrl:'templates/whosinclass.html',
        controller: 'WhosInClassCtrl'
    })
    .otherwise({
        redirectTo: '/'
    })
    ;
})
.controller('MainCtrl', function($scope) {
})
.controller('SigninCtrl', function($scope, $http, $location) {
    $scope.errorMessage = undefined;
    $scope.success = false;

    $scope.login = function(user) {
        $http.get('/signinout', {
            "params": {"username" : user.name}
        })
        .success(function(data,status) {
            if (data['is-child']) {
                $scope.student = {
                    username: data.username,
                    inClass: data['in-class']
                };
            } else {
                $scope.children = data.children;
            }
            $scope.success = true;
        }).error(function(data,status) {
            // 500 errors aren't our problem.
            if (status == 500) return;
            // if it's a 400 error, display the message to the client.
            if (status == 400) {
                $scope.errorMessage = data.message;
            }
        });
    };
})

.controller('WhosInClassCtrl', function($scope, $http) {
    $scope.students = {
        present: [],
        absent: [],
        nothere: []
    };
    $http.get('/whosinclass').success(function(data,status) {
        $scope.students.present = data.present || [];
        $scope.students.absent = data.absent || [];
        $scope.students.nothere = data.nothere || [];
  });
})
.controller('AdminUserDashCtrl', function($scope, $http, $location) {
    $scope.users = [];
    $http.get("/users").success(function(data) {
        $scope.users = data;
    });
    $scope.students = [];
    $http.get("/students").success(function(data) {
        $scope.students = data;
        console.log($scope.students);
    });

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
        if($scope.new_signers[name] !== null && $scope.new_signers[name] !== "") {
            console.log("Adding " + $scope.new_signers[name] + " to authorized signers.");
            $scope.students[name].authorized.push($scope.new_signers[name]);
            $http.put("/students/add-authorized", {"username": name, "signer": $scope.new_signers[name]});
        } else {
            console.log("That is empty or null!");
        }
    };

    $scope.remove_signer = function(student, signer) {
        console.log("Removing " + signer + " from " + student + "'s authorized signers.'");
        var i = $scope.students[student].authorized.indexOf(signer);
        if(i != -1) {
            $scope.students[student].authorized.splice(i, 1);
        }
        $http.put("/students/remove-authorized", {"username": student, "signer": signer});
    };
})
;
