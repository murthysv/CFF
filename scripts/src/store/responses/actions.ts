import { API } from "aws-amplify";
import { ResponsesState, IResponse } from "./types";
import { get, concat, assign } from "lodash-es";
import { flatten } from "flat";
import Headers from "../../admin/util/Headers";
import { loadingStart, loadingEnd } from "../base/actions";
import { push } from 'connected-react-router';

export const editResponse = (responseId, path, value) => (dispatch, getState) => {
  return API.patch("CFF", `responses/${responseId}`, {
    "body":
    {
      "path": path,
      "value": value
    }
  }).then(e => {
    if (e.res.success === true) {
      dispatch(setResponseDetail(e.res.response));
    }
  }).catch(e => {
    console.error(e);
    alert("Error updating value. " + e);
  });
};

export const fetchResponseDetail = (responseId) => (dispatch, getState) => {
  dispatch(loadingStart());
  return API.get("CFF", `responses/${responseId}`, {}).then(e => {
    dispatch(loadingEnd());
    dispatch(setResponseDetail(e.res));
  }).catch(e => {
    console.error(e);
    dispatch(loadingEnd());
    alert("Error updating value. " + e);
  });
};

export const setResponseDetail = (responseData: any) => ({
  type: 'SET_RESPONSE_DATA',
  responseData
});

export const onPaymentStatusDetailChange = (key: string, value: string) => ({
  type: 'CHANGE_PAYMENT_STATUS_DETAIL',
  key,
  value
});

export const clearPaymentStatusDetail = () => ({
  type: "CLEAR_PAYMENT_STATUS_DETAIL"
});

export const setResponses = (responses: IResponse[]) => ({
  type: "SET_RESPONSES",
  responses
});

export const setResponsesSelectedView = (viewName: string) => ({
  type: "SET_RESPONSES_SELECTED_VIEW",
  viewName
})


export const submitNewPayment = () => (dispatch, getState) => {
  dispatch(loadingStart());
  let responsesState: ResponsesState = getState().responses;
  return API.post("CFF", `responses/${responsesState.responseData._id.$oid}/payment`, {
    "body": responsesState.paymentStatusDetailItem
  }).then(e => {
    if (e.res.success === true) {
      dispatch(loadingEnd());
      dispatch(clearPaymentStatusDetail());
      dispatch(setResponseDetail(e.res.response));
    }
  }).catch(e => {
    dispatch(loadingEnd());
    console.error(e);
    alert("Error submitting new payment. " + e);
  });
};

export const fetchResponses = (formId) => (dispatch, getState) => {
  return API.get("CFF", `forms/${formId}/responses`, {}).then(e => {
    dispatch(setResponses(e.res));

  }).catch(e => {
    console.error(e);
    alert("Error fetching form responses. " + e);
  });
};