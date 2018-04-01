/// <reference path="./FormList.d.ts"/>
import * as React from 'react';
import axios from 'axios';
import { API } from 'aws-amplify';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import "./FormList.scss";

class FormList extends React.Component<IFormListProps, IFormListState> {
    constructor(props: any) {
        super(props);
        this.render = this.render.bind(this);
        this.state = {
            formList: null
        }
    }
    loadFormList() {
        return API.get("CFF", "centers/" + this.props.match.params.centerId + "/forms", {}).then(e => {
            this.setState({"formList": e.res});
        }).catch(e => {
            // this.setState({hasError: true});
        });
    }
    componentDidMount() {
        console.warn(this.props);
        this.loadFormList();
    }
    showEmbedCode(formId) {

    }
    render() {
        return (
            <table className="table table-hover table-sm table-responsive-sm">
                <thead>
                    <tr>
                        <th>Form name</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {this.state.formList && this.state.formList.map((form) =>
                        <tr key={form["id"]} style={{ outline: 'thin solid' }}>
                            <td>{form["name"]}</td>
                            <td>
                                <div className="btn-group btn-group-lg">
                                    {/*<button className="btn btn-primary" onClick = {() => this.props.embedForm(form)}>Embed</button>
                                    <button className="btn" onClick = {() => this.props.editForm(form)}>Edit</button>*/}
                                    <Link to={`${this.props.match.url}/${form.id}/responses`}><button className="btn">Responses</button></Link>
                                    {/*<button className="btn" onClick = {() => this.props.loadResponseSummary(form)}>Response Summary</button>*/}
                                </div>
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        )
    }
}
export default FormList;