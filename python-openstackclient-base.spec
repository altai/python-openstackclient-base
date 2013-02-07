%define mod_name openstackclient_base

%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%endif

Name:             python-openstackclient-base
Version:          2012.1
Release:          1%{?dist}
Epoch:            1
Summary:          OpenStack openstack Client

Group:            Development/Languages
License:          Apache 2.0
Vendor:           Grid Dynamics Consulting Services, Inc.
URL:              http://www.openstack.org
Source0:          %{name}-%{version}.tar.gz

BuildRoot:        %{_tmppath}/%{name}-%{version}

BuildArch:        noarch
BuildRequires:    python-setuptools

Obsoletes:        %{name}-essex

%description
This is a common API client library.


%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}

%{__python} setup.py install -O1 --skip-build --root %{buildroot}

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc README* LICENSE HACKING*
%{python_sitelib}/%{mod_name}
%{python_sitelib}/*.egg-info


%changelog
* Thu Jun 19 2012 Alessio Ababilov <aababilov@griddynamics.com> - 2012.1
- Initial release: spec created
